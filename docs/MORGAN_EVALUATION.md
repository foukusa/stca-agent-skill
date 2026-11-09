# How STCA evaluates new rules

[简体中文](MORGAN_EVALUATION.zh-CN.md) · [Usage](USAGE.md)

New learning uses an **interpolation/extrapolation split defined by Morgan distance**. The assistant performs the split and reports its evidence; you can use ordinary language throughout.

1. **Split by structure first.** Calculate 2,048-bit, radius=2 Morgan fingerprints (ECFP4) for H-capped calculation copies, with distance = 1 − Tanimoto similarity. Identical original repeat units and identical H-capped copies stay on the same side. Property values do not select the split.
2. **Separate extrapolation structures.** Select a peripheral structural neighborhood as the extrapolation region, targeting 20% of structurally valid records. Place other structural groups closer than 0.5 to it in a similarity buffer; the remainder forms the interpolation region. Every extrapolation structure must have nearest-neighbour distance **at least 0.5** from the interpolation region.
3. **Learn within the interpolation region.** Choose data transformations, scan step and support in this region. Use a further Morgan-distance validation inside it to compare STCA and WRAcc. Freeze the method recommendation before reading extrapolation results.
4. **Evaluate the frozen rules.** Use the training-derived numeric property cutoff and unit for both methods. Report extrapolation precision, recall, F1, Matthews correlation coefficient and the average screening score, together with sample counts and measured distances.
5. **Deliver reusable rules and screening.** Keep the trained rules and their thresholds. Screen the original uploaded table separately; its matches include training records and are reported separately from independent extrapolation performance.

The average screening score was introduced in the [STCA paper](https://doi.org/10.1038/s41524-026-02345-x): **(Matthews correlation coefficient + precision + F1) / 3**. When both methods have usable internal-validation evidence, WRAcc is recommended only when its score exceeds STCA's by more than 0.02; otherwise STCA is retained. Missing evidence is reported explicitly.

If the requested distance split cannot be formed, or the extrapolation region contains only one target class, the assistant reports the unavailable result and its reason. It does not silently substitute a random split. Small test sets and undefined metrics retain their actual status.

## Interpolation range, internal validation and extrapolation

| Data part | Split method | Purpose |
|---|---|---|
| Evaluation within the interpolation region | Protect identical original/H-capped structures as groups; random grouped fivefold cross-validation, repeated three times | Check performance within the interpolation range, using that region's data preparation; this is not a separate independent interpolation test set |
| Morgan validation inside the interpolation region | Further ECFP4 distance separation within the training region, with nearest-training distance ≥0.5 | Select STCA or WRAcc before extrapolation evaluation |
| Independent extrapolation region | Select a peripheral structural neighborhood, about 20% by default; a similarity buffer enforces nearest-neighbour distance ≥0.5 from the interpolation region | Test transfer to substantially different structures |

This prevents identical or highly similar structures from crossing the interpolation–extrapolation boundary and defines extrapolation through a measurable chemical-structure distance. The similarity buffer is excluded from training and extrapolation scoring, but its records are still screened. Morgan validation inside the interpolation region is distance-separated validation, distinct from its fivefold within-range evaluation. The current workflow does not provide a separate independent interpolation test set.

Bundled paper rules retain their original conditions and evaluation protocols.

A percentage defines the target tail of training labels, not a quota of selected candidates. Each percentage is prepared independently. Original `*` attachment points are retained in returned SMILES; H-capping is used only for calculation copies.
