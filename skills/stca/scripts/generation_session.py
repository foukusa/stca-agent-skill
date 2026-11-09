#!/usr/bin/env python3
"""Stage editable prompts and gate actual generation by the current AI assistant.

This standard-library helper never calls a model API.  The agent reads the
approved prompt, invokes its current LLM to propose structures, then uses the
unchanged frozen constraints to verify every proposal.  Review sessions require
an explicit user confirmation; elapsed time is never confirmation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from generation_prompt import render_prompt, resolve_structure_kind, STRUCTURE_KINDS


SCHEMA = "stca-generation-session-v1"
STATE_NAME = re.compile(r"session-state-([0-9]{8})\.json")
INTENT_NAME = re.compile(r"session-intent-([0-9]{8})\.json")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _read_json(path):
    def reject(value):
        raise ValueError(f"Nonfinite JSON value: {value}")
    return json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=reject)


def _session_path(path):
    path = Path(path).expanduser().resolve()
    return path / "session.json" if path.is_dir() else path


def _resource(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("Session resources must use relative paths.")
    path = (root / relative).resolve()
    if root not in path.parents or (root / relative).is_symlink():
        raise ValueError("Session resource escapes its directory or is a symlink.")
    return path


def _compose(constraints, state):
    # Old sessions predate output-notation metadata and retain their exact
    # repeat-unit prompt when reopened.
    kind = state.get("structure_kind", "polymer_repeat_unit")
    text = render_prompt(constraints, state["language"], state["requested_count"], state["preferences"], kind)
    if state["language"] == "zh-CN":
        notice = ("\n\n## 用户调整与执行约定\n\n"
                  "上述性质、阈值、精确 AND 条件、MACCS 语义及 H-cap 约定保持冻结。"
                  "下述调整用于数量以外的设计偏好、表达方式或输出要求；"
                  "如要求改变科学目标或冻结条件，先返回规则选择并建立新任务。\n\n")
    else:
        notice = ("\n\n## User adjustments and execution contract\n\n"
                  "The property targets, thresholds, exact AND conditions, MACCS semantics and H-cap convention above remain frozen. "
                  "Adjustments below describe design preferences, presentation or output requirements. "
                  "A changed scientific target or frozen condition requires a new rule selection and session.\n\n")
    draft = state["editable_instructions"].strip()
    return text.rstrip() + notice + (draft if draft else ("无额外调整。" if state["language"] == "zh-CN" else "No additional adjustments.")) + "\n"


def _create_json(path, value):
    """Create an immutable record; preserve permission and collision errors."""
    with path.open("xb") as stream:
        stream.write(_json_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def _state_chain(path):
    """Resolve any session handle to its latest complete, linked state.

    An intent is created before an update writes prompts. Incomplete updates
    therefore fail visibly instead of restoring an older generation approval.
    The original session.json remains readable and is never overwritten.
    """
    root = path.parent
    anchor = root / "session.json"
    if (root / "session.json.tmp").exists():
        raise ValueError("A legacy generation session update is incomplete; preserve its files and resolve the earlier write failure before continuing.")
    state = _read_json(anchor)
    if not isinstance(state, dict):
        raise ValueError("Unsupported generation session.")
    if (type(state.get("state_sequence", 1)) is not int or state.get("state_sequence", 1) != 1
            or state.get("previous_state_sha256") is not None):
        raise ValueError("Invalid initial generation session state.")
    paths, intents = {}, {}
    for pattern, expression, destination in (("session-state-*.json", STATE_NAME, paths),
                                              ("session-intent-*.json", INTENT_NAME, intents)):
        for resource in root.glob(pattern):
            match = expression.fullmatch(resource.name)
            if not match or resource.is_symlink():
                raise ValueError("Invalid generation session journal resource.")
            number = int(match.group(1))
            if number < 2 or number in destination:
                raise ValueError("Invalid generation session state sequence.")
            destination[number] = resource
    if set(paths) != set(intents):
        raise ValueError("Generation session update is incomplete; preserve its files and resolve the reported write failure before continuing.")
    previous = _sha(anchor.read_bytes())
    current = anchor
    for expected, number in enumerate(sorted(paths), 2):
        if number != expected:
            raise ValueError("Generation session state sequence has a gap.")
        intent = _read_json(intents[number])
        candidate = _read_json(paths[number])
        if (not isinstance(intent, dict) or intent.get("schema") != SCHEMA + "-intent"
                or type(intent.get("sequence")) is not int or intent.get("sequence") != number
                or intent.get("previous_state_sha256") != previous
                or intent.get("operation") not in {"revised", "confirmed"}
                or not isinstance(candidate, dict) or type(candidate.get("state_sequence")) is not int
                or candidate.get("state_sequence") != number
                or candidate.get("previous_state_sha256") != previous):
            raise ValueError("Generation session state history changed or is incomplete.")
        if candidate.get("constraints") != state.get("constraints") or candidate.get("mode") != state.get("mode"):
            raise ValueError("Frozen constraints or generation mode changed inside the session history.")
        revised = intent["operation"] == "revised"
        expected_revision = state["revision"] + (1 if revised else 0)
        expected_status = "awaiting_confirmation" if revised else "ready_to_generate"
        if (candidate.get("revision") != expected_revision or candidate.get("status") != expected_status
                or candidate.get("generation_allowed") is not (not revised)):
            raise ValueError("Generation session contains an invalid review or confirmation transition.")
        current, state = paths[number], candidate
        previous = _sha(current.read_bytes())
    return current, state


def _begin_state(path, state, operation):
    sequence = state.get("state_sequence", 1) + 1
    if sequence > 99999999:
        raise ValueError("Generation session state sequence limit reached.")
    previous = _sha(path.read_bytes())
    intent = path.parent / f"session-intent-{sequence:08d}.json"
    _create_json(intent, {"schema": SCHEMA + "-intent", "sequence": sequence,
                          "previous_state_sha256": previous, "operation": operation})
    return sequence, previous


def _write_state(path, state, pending=None):
    if pending is None:
        destination = path.parent / "session.json"
        state.update(state_sequence=1, previous_state_sha256=None)
    else:
        sequence, previous = pending
        destination = path.parent / f"session-state-{sequence:08d}.json"
        state.update(state_sequence=sequence, previous_state_sha256=previous)
    _create_json(destination, state)
    return destination


def _constraints(root, state):
    values = []
    records = state.get("constraints")
    if not isinstance(records, list) or not records:
        raise ValueError("Session has no frozen constraint snapshots.")
    for item in records:
        if not isinstance(item, dict):
            raise ValueError("Invalid frozen constraint snapshot record.")
        path = _resource(root, item["snapshot_path"])
        if _sha(path.read_bytes()) != item["sha256"]:
            raise ValueError("Frozen constraint snapshot changed; choose rules again in a new session.")
        value = _read_json(path)
        values.extend(value if isinstance(value, list) else [value])
    return values


def _load(path):
    path = _session_path(path)
    if path.name != "session.json" and STATE_NAME.fullmatch(path.name) is None:
        raise ValueError("Choose the session directory, session.json or a returned session state path.")
    if not path.is_file():
        raise FileNotFoundError(f"Generation session state does not exist: {path}")
    path, state = _state_chain(path)
    if not isinstance(state, dict) or state.get("schema") != SCHEMA or state.get("mode") not in {"preview", "direct"}:
        raise ValueError("Unsupported generation session.")
    if state.get("status") not in {"awaiting_confirmation", "ready_to_generate"}:
        raise ValueError("Unsupported generation session status.")
    if (isinstance(state.get("revision"), bool) or not isinstance(state.get("revision"), int)
            or state["revision"] < 1 or not isinstance(state.get("editable_instructions"), str)
            or not isinstance(state.get("history"), list)):
        raise ValueError("Invalid generation session revision or editable instructions.")
    root = path.parent
    constraints = _constraints(root, state)
    expected = _compose(constraints, state).encode("utf-8")
    prompt = _resource(root, state["prompt_path"])
    if prompt.read_bytes() != expected or _sha(expected) != state["current_prompt_sha256"]:
        raise ValueError("Prompt content changed outside revision; revise the session before continuing.")
    ready = state["status"] == "ready_to_generate"
    if bool(state.get("generation_allowed")) != ready:
        raise ValueError("Generation authorization conflicts with session status.")
    if ready:
        approved = _resource(root, state["approved_prompt_path"])
        if (approved.read_bytes() != expected or state["approved_prompt_sha256"] != _sha(expected)
                or state.get("approved_revision") != state["revision"]):
            raise ValueError("Approved prompt changed or approval belongs to an earlier revision.")
    elif any(state.get(key) is not None for key in ("approved_prompt_path", "approved_prompt_sha256", "approved_revision")):
        raise ValueError("An unconfirmed session cannot retain approval.")
    return path, state, constraints


def _write_prompt(root, state, constraints):
    data = _compose(constraints, state).encode("utf-8")
    state["prompt_path"] = f"prompt-revision-{state['revision']:04d}.md"
    with _resource(root, state["prompt_path"]).open("xb") as stream:
        stream.write(data)
    state["current_prompt_sha256"] = _sha(data)


def _authorize(root, state, evidence):
    data = _resource(root, state["prompt_path"]).read_bytes()
    state["approved_prompt_path"] = f"approved-prompt-revision-{state['revision']:04d}.md"
    with _resource(root, state["approved_prompt_path"]).open("xb") as stream:
        stream.write(data)
    state.update(status="ready_to_generate", generation_allowed=True,
                 approved_prompt_sha256=_sha(data), approved_revision=state["revision"],
                 authorization=evidence)


def _response(path, state, include_prompt=False):
    root = path.parent
    ready = state["generation_allowed"]
    result = dict(state)
    result.setdefault("structure_kind", "polymer_repeat_unit")
    result.update(session_path=str(path), prompt_path=str(_resource(root, state["prompt_path"])),
                  approved_prompt_path=(str(_resource(root, state["approved_prompt_path"])) if ready else None),
                  next_action="invoke_current_llm_and_verify" if ready else "show_full_prompt_and_wait_for_user_confirmation",
                  executor="current_ai_assistant", api_configuration_required=False,
                  generation_performed=False, verification_performed=False)
    if include_prompt:
        result["prompt"] = _resource(root, state["prompt_path"]).read_text(encoding="utf-8")
    return result


def prepare_session(constraint_paths, output_dir, *, mode, count=20, preferences="", language="zh-CN",
                    structure_kind=None):
    if mode not in {"preview", "direct"}:
        raise ValueError("mode must be preview or direct.")
    output = Path(output_dir).expanduser().resolve()
    if output.exists():
        raise ValueError("Output directory exists; choose a new generation session directory.")
    values, snapshots = [], []
    for index, value in enumerate(constraint_paths, 1):
        path = Path(value).expanduser().resolve()
        data = path.read_bytes()
        constraint = _read_json(path)
        values.extend(constraint if isinstance(constraint, list) else [constraint])
        snapshots.append((f"constraints-{index:02d}.json", data))
    state = {"schema": SCHEMA, "mode": mode, "status": "awaiting_confirmation",
             "generation_allowed": False, "revision": 1, "language": language,
             "structure_kind": resolve_structure_kind(values, structure_kind),
             "requested_count": count, "preferences": preferences, "editable_instructions": "",
             "approved_prompt_path": None, "approved_prompt_sha256": None,
             "approved_revision": None, "authorization": None,
             "constraints": [{"snapshot_path": name, "sha256": _sha(data)} for name, data in snapshots],
             "history": [{"event": "prepared", "at": _now(), "mode": mode}]}
    # All validation occurs before creating output artifacts.
    _compose(values, state)
    output.mkdir(parents=True)
    for name, data in snapshots:
        with (output / name).open("xb") as stream:
            stream.write(data)
    _write_prompt(output, state, values)
    if mode == "direct":
        _authorize(output, state, {"kind": "direct_mode_requested", "at": _now()})
    path = output / "session.json"
    path = _write_state(path, state)
    return _response(path, state)


def revise_session(session, *, count=None, preferences=None, draft_file=None, structure_kind=None):
    path, state, constraints = _load(session)
    if all(value is None for value in (count, preferences, draft_file, structure_kind)):
        raise ValueError("Supply a count, preferences, editable draft file or structure kind.")
    if count is not None:
        state["requested_count"] = count
    if preferences is not None:
        state["preferences"] = preferences
    if draft_file is not None:
        state["editable_instructions"] = Path(draft_file).read_text(encoding="utf-8-sig")
    state["structure_kind"] = resolve_structure_kind(
        constraints, structure_kind if structure_kind is not None else state.get("structure_kind", "polymer_repeat_unit"))
    _compose(constraints, state)
    state.update(revision=state["revision"] + 1, status="awaiting_confirmation", generation_allowed=False,
                 approved_prompt_path=None, approved_prompt_sha256=None, approved_revision=None, authorization=None)
    state["history"].append({"event": "revised", "at": _now(), "revision": state["revision"]})
    pending = _begin_state(path, state, "revised")
    _write_prompt(path.parent, state, constraints)
    path = _write_state(path, state, pending)
    return _response(path, state)


def confirm_session(session, *, confirmation_text):
    if not isinstance(confirmation_text, str) or not confirmation_text.strip():
        raise ValueError("Explicit observed user confirmation text is required; time or silence is not approval.")
    path, state, _ = _load(session)
    if not state["generation_allowed"]:
        pending = _begin_state(path, state, "confirmed")
        _authorize(path.parent, state, {"kind": "explicit_user_confirmation",
                                     "text": confirmation_text.strip(), "at": _now()})
        state["history"].append({"event": "confirmed", "at": _now(), "revision": state["revision"]})
        path = _write_state(path, state, pending)
    return _response(path, state)


def session_status(session, *, include_prompt=False):
    path, state, _ = _load(session)
    return _response(path, state, include_prompt)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    prepare = actions.add_parser("prepare")
    prepare.add_argument("--constraints", type=Path, nargs="+", action="extend", required=True)
    prepare.add_argument("--mode", choices=("preview", "direct"), required=True)
    prepare.add_argument("--count", type=int, default=20)
    prepare.add_argument("--preferences", default="")
    prepare.add_argument("--language", choices=("zh-CN", "en"), default="zh-CN")
    prepare.add_argument("--structure-kind", choices=STRUCTURE_KINDS)
    prepare.add_argument("--output-dir", type=Path, required=True)
    revise = actions.add_parser("revise")
    revise.add_argument("--session", type=Path, required=True)
    revise.add_argument("--count", type=int)
    revise.add_argument("--preferences")
    revise.add_argument("--draft-file", type=Path)
    revise.add_argument("--structure-kind", choices=STRUCTURE_KINDS)
    confirm = actions.add_parser("confirm")
    confirm.add_argument("--session", type=Path, required=True)
    confirm.add_argument("--confirmation-text", required=True,
                         help="Exact user confirmation observed in the conversation; never synthesize consent.")
    status = actions.add_parser("status")
    status.add_argument("--session", type=Path, required=True)
    status.add_argument("--include-prompt", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action == "prepare":
            result = prepare_session(args.constraints, args.output_dir, mode=args.mode,
                                     count=args.count, preferences=args.preferences, language=args.language,
                                     structure_kind=args.structure_kind)
        elif args.action == "revise":
            result = revise_session(args.session, count=args.count, preferences=args.preferences,
                                    draft_file=args.draft_file, structure_kind=args.structure_kind)
        elif args.action == "confirm":
            result = confirm_session(args.session, confirmation_text=args.confirmation_text)
        else:
            result = session_status(args.session, include_prompt=args.include_prompt)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"generation_session: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
