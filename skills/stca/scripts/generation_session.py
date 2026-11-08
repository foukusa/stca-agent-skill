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
from pathlib import Path
import sys

from generation_prompt import render_prompt


SCHEMA = "stca-generation-session-v1"


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
    text = render_prompt(constraints, state["language"], state["requested_count"], state["preferences"])
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


def _write_state(path, state):
    temporary = path.with_name("session.json.tmp")
    with temporary.open("xb") as stream:
        stream.write(_json_bytes(state))
    temporary.replace(path)


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
    state = _read_json(path)
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
    result.update(session_path=str(path), prompt_path=str(_resource(root, state["prompt_path"])),
                  approved_prompt_path=(str(_resource(root, state["approved_prompt_path"])) if ready else None),
                  next_action="invoke_current_llm_and_verify" if ready else "show_full_prompt_and_wait_for_user_confirmation",
                  executor="current_ai_assistant", api_configuration_required=False,
                  generation_performed=False, verification_performed=False)
    if include_prompt:
        result["prompt"] = _resource(root, state["prompt_path"]).read_text(encoding="utf-8")
    return result


def prepare_session(constraint_paths, output_dir, *, mode, count=20, preferences="", language="zh-CN"):
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
             "requested_count": count, "preferences": preferences, "editable_instructions": "",
             "approved_prompt_path": None, "approved_prompt_sha256": None,
             "approved_revision": None, "authorization": None,
             "constraints": [{"snapshot_path": name, "sha256": _sha(data)} for name, data in snapshots],
             "history": [{"event": "prepared", "at": _now(), "mode": mode}]}
    # All validation occurs before creating output artifacts.
    _compose(values, state)
    output.mkdir(parents=True)
    for name, data in snapshots:
        (output / name).write_bytes(data)
    _write_prompt(output, state, values)
    if mode == "direct":
        _authorize(output, state, {"kind": "direct_mode_requested", "at": _now()})
    path = output / "session.json"
    _write_state(path, state)
    return _response(path, state)


def revise_session(session, *, count=None, preferences=None, draft_file=None):
    path, state, constraints = _load(session)
    if all(value is None for value in (count, preferences, draft_file)):
        raise ValueError("Supply a count, preferences or editable draft file.")
    if count is not None:
        state["requested_count"] = count
    if preferences is not None:
        state["preferences"] = preferences
    if draft_file is not None:
        state["editable_instructions"] = Path(draft_file).read_text(encoding="utf-8-sig")
    _compose(constraints, state)
    state.update(revision=state["revision"] + 1, status="awaiting_confirmation", generation_allowed=False,
                 approved_prompt_path=None, approved_prompt_sha256=None, approved_revision=None, authorization=None)
    state["history"].append({"event": "revised", "at": _now(), "revision": state["revision"]})
    _write_prompt(path.parent, state, constraints)
    _write_state(path, state)
    return _response(path, state)


def confirm_session(session, *, confirmation_text):
    if not isinstance(confirmation_text, str) or not confirmation_text.strip():
        raise ValueError("Explicit observed user confirmation text is required; time or silence is not approval.")
    path, state, _ = _load(session)
    if not state["generation_allowed"]:
        _authorize(path.parent, state, {"kind": "explicit_user_confirmation",
                                     "text": confirmation_text.strip(), "at": _now()})
        state["history"].append({"event": "confirmed", "at": _now(), "revision": state["revision"]})
        _write_state(path, state)
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
    prepare.add_argument("--output-dir", type=Path, required=True)
    revise = actions.add_parser("revise")
    revise.add_argument("--session", type=Path, required=True)
    revise.add_argument("--count", type=int)
    revise.add_argument("--preferences")
    revise.add_argument("--draft-file", type=Path)
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
                                     count=args.count, preferences=args.preferences, language=args.language)
        elif args.action == "revise":
            result = revise_session(args.session, count=args.count, preferences=args.preferences, draft_file=args.draft_file)
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
