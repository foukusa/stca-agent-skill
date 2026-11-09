# OpenPoly water contact angle

[简体中文](README.zh-CN.md) · [Main README](../../README.md)

Use a polymer surface property to try STCA: learn readable rules from public water-contact-angle data, save them, and reuse them to screen candidates or guide LLM generation of repeat units.

## Contents

- [Data and columns](#data-and-columns)
- [Learn rules and screen](#learn-rules-and-screen)
- [Reproducible extrapolation case](#reproducible-extrapolation-case)
- [Reuse rules and generate](#reuse-rules-and-generate)
- [Sources](#sources)

## Data and columns

Download [OpenPoly.csv](OpenPoly.csv) from this directory and upload it to a conversation with STCA installed. The original file has **741 rows and 32 columns**, including **175 rows** with water-contact-angle labels. Upload the complete file; the assistant reads usable labels from the specified target column and explains how unlabeled rows are handled.

| Purpose | Original column | Position |
|---|---|---|
| Optional name | `Name` | A · column 1 |
| Polymer repeat unit | `PSMILES` | B · column 2 |
| Water contact angle, degrees | `Water Contact Angle (deg)` | Y · column 25 |

Row 1 contains headers; rows 2–742 contain data. `PSMILES_2` and `PSMILES_4` contain expanded repeat-unit representations; this example uses the original `PSMILES`. **0° is a valid value for complete wetting.** Results preserve the original attachment-point stars; H-cap is used only in a separate calculation copy.

## Learn rules and screen

Upload the CSV and send:

```text
Learn high water-contact-angle Top 30% rules from this OpenPoly file. Use PSMILES and Water Contact Angle (deg), in degrees. Return Morgan-distance extrapolation evaluation and screening results, then save the rules.
```

After splitting structures, STCA selects transformations, scan settings and support using the training portion only, and learns separate STCA and WRAcc rules. Extrapolation evaluation requires every held-out structure to have a nearest-training ECFP4 Tanimoto distance of at least **0.5**; boundary structures that are too close are marked separately. Both methods return screening decisions for the original table, together with the numerical angle threshold and comparator for Top 30%.

You can request low contact angles or another percentage, such as Top 15% or 20%. Omitted percentages default to 10%, 20% and 30%. Percentages define the property target boundary; structure rules determine how many candidates match.

## Reproducible extrapolation case

The bundled rules were learned from the pinned file above. Its 740 supported structures were split into **461 training records, 148 held-out records and a 131-record distance buffer**; one further structure could not be calculated under the current H-cap contract. Source preparation retained **104 labeled observations**. The holdout contains **31 records** with contact-angle labels; its other 117 records do not contribute to property scores. Every held-out structure has nearest-training distance **≥ 0.5**, with median **0.5914**.

| Target | Frozen angle threshold | Training-side recommendation |
|---|---:|---|
| Top 10% | ≥ 104.17491015° | STCA |
| Top 20% | ≥ 97.368824894° | WRAcc |
| Top 30% | ≥ 87.714722219° | STCA |

Top 30% results on the 31 labeled holdout records are below; 11 meet the property threshold:

| Method | Matches / true positives | Precision | Recall | F1 | Matthews correlation coefficient |
|---|---:|---:|---:|---:|---:|
| STCA | 4 / 2 | 0.5000 | 0.1818 | 0.2667 | 0.1168 |
| WRAcc | 5 / 3 | 0.6000 | 0.2727 | 0.3750 | 0.2247 |

Recommendations are fixed using a further strict Morgan holdout inside the training portion; outer results do not change them. WRAcc scores higher on this Top 30% outer holdout, and both rules remain selectable. See [this case's evaluation table](evaluation.csv) and [all public tasks](../open_data/current_morgan_cases.csv) for all three tiers and both methods.

When screening the original 741 rows, the Top 30% STCA and WRAcc rules match **172 and 281 records**, respectively, with one unknown each. These counts include structures without contact-angle labels and are not counts of measured high-contact-angle polymers. This case demonstrates learning, saving and reusing rules; strict distant-structure screening still misses positives.

## Reuse rules and generate

After saving the rules, continue with:

```text
Use the recommended high-water-contact-angle rule I just saved to screen this new candidate table.
```

You can also choose a bundled OpenPoly water-contact-angle rule; the assistant shows the relevant percentages and available methods before applying your selection.

```text
Use the Top 30% STCA rule I just saved to directly generate and verify 10 polymer repeat units.
```

To adjust the generation constraints first, say “Show the complete generation prompt without generating yet,” then reply “Confirm and generate” after editing it. Rule verification checks structural conditions; actual contact angles of new candidates require subsequent measurement.

## Sources

- [Official OpenPoly repository](https://github.com/WangGroupFDU/Openpoly_benchmark) · [Original data file](https://github.com/WangGroupFDU/Openpoly_benchmark/blob/ccaa66900747bfc576ef935e3d5f220b6c9b1f85/data/final_polymer_properties_fromliterature.csv).
- [OpenPoly research paper](https://doi.org/10.1007/s10118-025-3402-y).
- The CSV is byte-identical to the pinned public file; see [source and column records](source.json). The original [MIT license](OpenPoly_LICENSE.txt) accompanies the file.

Water contact angle is a surface property. This CSV does not supply surface treatment, roughness or measurement conditions per record; include these conditions when available in your own data.
