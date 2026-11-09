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

## Within-range diagnostics, internal validation and extrapolation

| Data part | Split | Purpose |
|---|---|---|
| Within-source diagnostic | Protect identical original/H-cap structures as groups; random grouped fivefold CV, repeated three times | Check the same source distribution, conditional on its preparation settings; this is not a separate interpolation test |
| Source-inner Morgan validation | Further ECFP4 distance holdout within source, with nearest-training distance ≥ 0.5 | Select STCA or WRAcc before outer evaluation |
| Independent outer holdout | Select a peripheral structural neighborhood, about 20% by default; place other groups closer than 0.5 to it in buffer and use the remainder as source | Test transfer to substantially different structures |

This protects against identical or highly similar structures crossing training and evaluation, and defines extrapolation through a measurable chemical-structure distance. The buffer enforces that boundary. Its rows are still screened but do not train or score the rules. Source-inner Morgan validation is also a distance holdout, not interpolation; the current workflow does not provide a separate distance-defined interpolation test set.

The STCA-paper frozen rules retain their original conditions and evaluation protocol.

A percentage defines a source-label tail, not a quota of selected candidates. Each percentage is prepared independently. Original `*` attachment points are retained in returned SMILES; H-cap is used only for calculation copies.
