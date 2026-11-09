# Changelog

## 0.1.0 — updated 2026-11-09

- Preserve original polymer connection graphs and star-containing SMILES; H-cap is calculation-only.
- Prepare, select scan settings, validate and fit each requested percentage independently, so adding or reordering tiers does not change an existing tier.
- Refresh open-data rules for 12 property tasks using the same workflow as natural-language learning. Keep 11 paper rules and 72 current method results; remove 138 superseded profiles from the distribution.
- Return both STCA and WRAcc results, physical cutoffs, availability, the recommended method and reusable rule bundles. RadonPy density Top 30% recommends WRAcc.
- Support custom percentages, automatic Python discovery, editable complete bilingual prompts, LLM generation and per-candidate verification.
- Save user-created rules separately and support exporting, importing and screening them again.
- Export WorkBuddy 0.1.3 with a two-level layout and an enforced 3 MiB expanded-size limit. Include a directly inspectable author_source directory and verify all its resources against the complete runtime payload.
- Make source and license declarations match the physical layout of every platform package.
- Use the GitHub shorthand for DSH GUI installation, include complete npm/plugin resources, and exclude Python caches.
- Ship native Codex/ChatGPT skill packages, DSH plugin and standalone packages, the WorkBuddy upload package, bilingual documentation, logo and workflow figures.
