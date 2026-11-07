# Changelog

## 0.1.0 — prepared 2026-11-07

This is the first prepared release of the agent integration. Its preparation date is not a claim that a public repository, plugin listing or software DOI has already been published.

### Included

- Three workflows: published-rule screening; measured-data fitting, freezing and evaluation; host-agent candidate proposals followed by executed rule checks.
- The original author implementation pinned to commit `5951b0ef23d63edc8f7e803aaaffa5e4168288f6` (polymer-stca 1.0).
- Explicit H-cap preparation that preserves original inputs and writes a separate calculation column.
- Strict CSV parsing that preserves textual identifiers and rejects inconsistent record widths.
- Explicit `paper` and `source_locked` protocol handling.
- Exact rule/prompt export and same-candidate multi-property structural intersections.
- A ten-candidate public fixture, per-candidate expected results and executable regression checks.
- Aggregate validation records without original measured per-material data.

### Corrected before release

- Restored original paper low-EC 5% reproduction: source/extra/all selections are 328/61/389 on the 691/172 original split.
- Separated the 33-condition source-only representative from the 12-condition original paper representative.
- Applied the confirmed H-cap representation to the candidate workflow; the unchanged ten proposals yield nine EC5 matches, with P10 rejected by K124.
- Repaired wrapper handling of family import, named-protocol provenance and generic binary-feature explanations.

### Scope

No original STCA ranking-prefix algorithm or representative-selection formula was changed. The proposal model belongs to the host agent. Candidate rule matches are not experimental property measurements or verified new materials. Public platform installation and any future runtime changes should be validated on their actual target surface.
