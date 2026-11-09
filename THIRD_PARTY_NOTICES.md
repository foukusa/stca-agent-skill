# Third-party notices

## Original STCA implementation

- Project: polymer-stca
- Author implementation: <https://github.com/foukusa/polymer-stca>
- Pinned source revision: `5951b0ef23d63edc8f7e803aaaffa5e4168288f6`
- Package version at this revision: `1.0`
- License source: <https://github.com/foukusa/polymer-stca/blob/5951b0ef23d63edc8f7e803aaaffa5e4168288f6/LICENSE>

The agent integration calls this pinned implementation. The unchanged author source and required packaged model/resources are included with the original license, attribution notice, and per-file integrity manifest. Runtime verification checks these contents before importing them; ordinary calculations do not need Git or a separate source download. Original measured research tables are not included. Extracted frozen structure conditions and generation prompts retain their rule and data-source provenance. Use and redistribution of the author implementation remain subject to the original terms below.

The upstream LICENSE at the pinned revision is reproduced unchanged below:

```text
Copyright (c) 2025, The University of Tokyo, University College London

Permission is granted to use and modify this software for non-commercial academic research, education, and reproduction of scientific results.

Commercial use and redistribution, including distribution of modified versions, require prior written permission from the copyright holders.

This copyright notice and license text must be retained in copies of the software.

The software is provided "AS IS", without warranty of any kind. The copyright holders are not liable for claims or damages arising from its use.
```

The notice above applies only to the upstream software. The newly written STCA Agent Skill integration, documentation, examples, validation records, and bundled logo are governed by the repository-level `LICENSE`. No broader permission for the upstream implementation is asserted by the integration license.

## Python and scientific dependencies

The execution environment uses Python, NumPy, pandas, SciPy and RDKit, together with their dependencies. The release does not bundle their interpreter or package binaries. When installing them, retain the license and notice files distributed with the selected packages. If a later release bundles an environment or wheels, include and review the notices for those actual distributions, rather than relying on this dependency list as a substitute.

## Research attribution

Weihao Wang, Haoou Ruan, Keith T. Butler, Akiko Kumada and Masahiro Sato. *Interpretable substructure-based screening of multi-property polymer dielectrics with prompt-ready rules for rational design.* npj Computational Materials (2026). <https://doi.org/10.1038/s41524-026-02345-x>.

The agent-generated demonstration candidates have no measured-property labels and make no claim of chemical novelty.

## OpenPoly example data

The repository includes the public literature-property table from [OpenPoly](https://github.com/WangGroupFDU/Openpoly_benchmark), associated with DOI 10.1007/s10118-025-3402-y, under the upstream MIT license. The original license accompanies the redistributed table. Standalone platform skill packages contain rule metadata and source links; they do not contain this raw table. The original STCA paper measurement tables are not redistributed.

## Included source files

The author implementation is included in `skills/stca/assets/author_source`. Original license and attribution files: `skills/stca/assets/author_source/LICENSE` and `skills/stca/assets/author_source/NOTICE`. The unchanged original file-integrity manifest is `skills/stca/assets/author_source/source_manifest.json`.
