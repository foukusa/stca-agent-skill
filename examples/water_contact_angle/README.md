# Supported property: water contact angle

[简体中文](README.zh-CN.md) · [Existing-rule catalog](../../docs/RULE_LIBRARY.md#openpoly-water-contact-angle)

OpenPoly water contact angle extends the property coverage of the STCA catalog. Top 10%, 20% and 30% STCA and WRAcc rules retain their actual evaluation results.

## Source data

[OpenPoly.csv](OpenPoly.csv) is a literature-property table with 741 rows and 32 columns; 175 rows have water-contact-angle labels. Use `PSMILES` (B/column 2) and `Water Contact Angle (deg)` (Y/column 25), in degrees. `PSMILES_2` and `PSMILES_4` are not used for this entry. A 0° value is valid complete wetting.

Source: [original OpenPoly table](https://github.com/WangGroupFDU/Openpoly_benchmark/blob/ccaa66900747bfc576ef935e3d5f220b6c9b1f85/data/final_polymer_properties_fromliterature.csv) · [study](https://doi.org/10.1007/s10118-025-3402-y) · [original MIT license](OpenPoly_LICENSE.txt). Measurement conditions are not supplied in the table.

## Three tiers and recorded results

The structural split contains 461 source, 148 holdout and 131 buffer rows, with one unsupported structure. Preparation retains 104 labeled source observations; 31 holdout rows have labels for scoring. Every holdout has nearest-source ECFP4 distance ≥ 0.5.

| Target | Frozen angle cutoff | Method | Precision | Recall | F1 | MCC |
|---|---:|---|---:|---:|---:|---:|
| Top30% | ≥87.714722219° | STCA | 0.5000 | 0.1818 | 0.2667 | 0.1168 |
| Top30% | ≥87.714722219° | WRAcc | 0.6000 | 0.2727 | 0.3750 | 0.2247 |
| Top20% | ≥97.368824894° | STCA | 0.0000 | 0.0000 | 0.0000 | -0.2079 |
| Top20% | ≥97.368824894° | WRAcc | 0.0000 | 0.0000 | 0.0000 | -0.2368 |
| Top10% | ≥104.17491015° | STCA | 0.0000 | 0.0000 | 0.0000 | -0.1886 |
| Top10% | ≥104.17491015° | WRAcc | 1.0000 | 0.5000 | 0.6667 | 0.6682 |

Choose exact conditions and complete prompts from the existing-rule catalog. See [evaluation.csv](evaluation.csv) and [source record](source.json) for details. Original attachment-point SMILES are retained; H-cap is a calculation copy.
