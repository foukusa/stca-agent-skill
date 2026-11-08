# Third-party notices

## Original STCA implementation

- Project: polymer-stca
- Author implementation: <https://github.com/foukusa/polymer-stca>
- Pinned source revision: `5951b0ef23d63edc8f7e803aaaffa5e4168288f6`
- Package version at this revision: `1.0`
- License source: <https://github.com/foukusa/polymer-stca/blob/5951b0ef23d63edc8f7e803aaaffa5e4168288f6/LICENSE>

The agent integration calls this pinned implementation. The original algorithm source, full pretrained model files and measured research tables are not vendored into the skill package. The skill includes extracted frozen structure conditions and generation prompts, with their rule and data-source provenance. Initial setup obtains the author repository separately. Obtaining or using that repository remains subject to its terms.

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

The public fixture contains agent-proposed structures with no measured-property labels. It is not a redistribution of the original measured polymer dataset and does not claim that the proposed structures are chemically novel.
