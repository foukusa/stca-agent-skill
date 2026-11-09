# How STCA evaluates new rules

[简体中文](MORGAN_EVALUATION.zh-CN.md) · [Usage](USAGE.md)

New learning uses a **strict Morgan-distance holdout**. The assistant performs the split and reports its evidence; you can use ordinary language throughout.

1. **Split by structures first.** Compute 2,048-bit radius-2 Morgan fingerprints (ECFP4) from H-cap calculation copies. Keep identical original repeat units and identical H-cap copies together. Property values do not choose the split.
2. **Separate distant structures.** Every holdout structure must have nearest-neighbour Tanimoto distance **at least 0.5** from the source structures. Boundary records may form a reported buffer; buffer records are excluded from fitting and holdout scoring.
3. **Learn within source.** Choose data transformations, scan step and support using source data. Use a further Morgan-distance validation inside source to compare STCA and WRAcc. Freeze the method recommendation before reading outer holdout results.
4. **Evaluate the frozen rules.** Use the source-derived numeric property cutoff and unit for both methods. Report holdout precision, recall, F1, Matthews correlation coefficient and the average screening score, together with sample counts and measured distances.
5. **Deliver reusable rules and screening.** Keep the source-trained rules and their thresholds. Screen the original uploaded table separately; its matches include training records and are not the holdout performance estimate.

The average screening score was introduced in the [STCA paper](https://doi.org/10.1038/s41524-026-02345-x): **(Matthews correlation coefficient + precision + F1) / 3**. When both methods have usable source-validation evidence, WRAcc is recommended only when its score exceeds STCA's by more than 0.02; otherwise STCA is retained. Missing evidence is reported explicitly.

If the requested distance split cannot be formed, or a holdout contains only one target class, the assistant reports the unavailable result and its reason. It does not silently substitute a random split. Small test sets and undefined metrics retain their actual status.

Earlier protected-group random fivefold results describe evaluation within the observed data distribution. Earlier ECFP4–t-SNE peripheral splits describe that projection-based protocol. Neither is relabelled as a strict Morgan-distance test. The STCA-paper frozen rules retain their original rules and evaluation protocol.

A percentage defines a source-label tail, not a quota of selected candidates. Each percentage is prepared independently. Original `*` attachment points are retained in returned SMILES; H-cap is used only for calculation copies.
