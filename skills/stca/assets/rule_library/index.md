# STCA rule and prompt library

> Tg/EC来源说明：这11条冻结条件来自作者SI-20260822归档快照；不表示正式论文全量数字复现。Tg Top10%为归档代表变体，与正式SI S7.1所述最优family不同。原条件保留，来源状态见catalog publication_alignment。


83 visible choices from 149 retained frozen entries. Version 0.1.0.

The visible library contains 11 published-profile rules and 72 supplied full-data rules: 12 datasets × 3 target tiers × 2 learners. Select a dataset, learner and tier explicitly. Each rule is an exact AND conjunction; primary/alternative denotes learner choice by grouped cross-validation and does not merge their conditions.

The latest 36 dataset/tier choices have 15 STCA and 21 WRAcc primary rules. The other 36 learner rules remain visible as alternatives. CV mean/SD, full-data screening support and optional extrapolation evidence are separate. Physical cutoffs define training-label boundaries, not property predictions or coverage guarantees.

The 66 older non-paper entries retain their IDs, files and original evidence for explicit compatibility lookup; they are marked legacy and hidden from default menus. Their extrapolation or historical zero-coverage statuses do not apply to the new full-data rules.

| Rule ID | Dataset / target | Learner / role | Tier / physical boundary | CV AS | Full-data selected |
|---|---|---|---|---:|---:|
| `paper-tg-high-30` | STCA paper · Glass-transition temperature | STCA published profile | Top 30% | published evidence | — |
| `paper-tg-high-20` | STCA paper · Glass-transition temperature | STCA published profile | Top 20% | published evidence | — |
| `paper-tg-high-10` | STCA paper · Glass-transition temperature | STCA published profile | Top 10% | published evidence | — |
| `paper-ec-low-20` | STCA paper · Electrical conductivity | STCA published profile | Bottom 20% | published evidence | — |
| `paper-ec-low-15` | STCA paper · Electrical conductivity | STCA published profile | Bottom 15% | published evidence | — |
| `paper-ec-low-10` | STCA paper · Electrical conductivity | STCA published profile | Bottom 10% | published evidence | — |
| `paper-ec-low-5` | STCA paper · Electrical conductivity | STCA published profile | Bottom 5% | published evidence | — |
| `paper-ec-high-20` | STCA paper · Electrical conductivity | STCA published profile | Top 20% | published evidence | — |
| `paper-ec-high-15` | STCA paper · Electrical conductivity | STCA published profile | Top 15% | published evidence | — |
| `paper-ec-high-10` | STCA paper · Electrical conductivity | STCA published profile | Top 10% | published evidence | — |
| `paper-ec-high-5` | STCA paper · Electrical conductivity | STCA published profile | Top 5% | published evidence | — |
| `latest-gas-co2-stca-high-30` | GAS_CO2 · CO2 permeability | STCA / primary | Top 30%; ≥ 526.9799741241644 Barrer | 0.602 ± 0.039 | 69 |
| `latest-gas-co2-wracc-high-30` | GAS_CO2 · CO2 permeability | WRAcc / alternative | Top 30%; ≥ 526.9799741241644 Barrer | 0.600 ± 0.023 | 88 |
| `latest-gas-co2-stca-high-20` | GAS_CO2 · CO2 permeability | STCA / primary | Top 20%; ≥ 2199.9999999999995 Barrer | 0.609 ± 0.016 | 32 |
| `latest-gas-co2-wracc-high-20` | GAS_CO2 · CO2 permeability | WRAcc / alternative | Top 20%; ≥ 2199.9999999999995 Barrer | 0.541 ± 0.019 | 85 |
| `latest-gas-co2-stca-high-10` | GAS_CO2 · CO2 permeability | STCA / primary | Top 10%; ≥ 5309.630036708536 Barrer | 0.635 ± 0.078 | 32 |
| `latest-gas-co2-wracc-high-10` | GAS_CO2 · CO2 permeability | WRAcc / alternative | Top 10%; ≥ 5309.630036708536 Barrer | 0.542 ± 0.032 | 35 |
| `latest-gas-o2-stca-high-30` | GAS_O2 · O2 permeability | STCA / primary | Top 30%; ≥ 60.7285939633838 Barrer | 0.638 ± 0.024 | 85 |
| `latest-gas-o2-wracc-high-30` | GAS_O2 · O2 permeability | WRAcc / alternative | Top 30%; ≥ 60.7285939633838 Barrer | 0.635 ± 0.040 | 116 |
| `latest-gas-o2-stca-high-20` | GAS_O2 · O2 permeability | STCA / primary | Top 20%; ≥ 203.080764076594 Barrer | 0.582 ± 0.034 | 22 |
| `latest-gas-o2-wracc-high-20` | GAS_O2 · O2 permeability | WRAcc / alternative | Top 20%; ≥ 203.080764076594 Barrer | 0.600 ± 0.026 | 87 |
| `latest-gas-o2-stca-high-10` | GAS_O2 · O2 permeability | STCA / primary | Top 10%; ≥ 967.4524402529456 Barrer | 0.729 ± 0.038 | 22 |
| `latest-gas-o2-wracc-high-10` | GAS_O2 · O2 permeability | WRAcc / alternative | Top 10%; ≥ 967.4524402529456 Barrer | 0.466 ± 0.010 | 68 |
| `latest-pi-tc-stca-high-30` | PI_TC · Thermal conductivity | STCA / primary | Top 30%; ≥ 0.2582924293999999 W/(m K) | 0.520 ± 0.025 | 172 |
| `latest-pi-tc-wracc-high-30` | PI_TC · Thermal conductivity | WRAcc / alternative | Top 30%; ≥ 0.2582924293999999 W/(m K) | 0.460 ± 0.008 | 605 |
| `latest-pi-tc-stca-high-20` | PI_TC · Thermal conductivity | STCA / primary | Top 20%; ≥ 0.277747882 W/(m K) | 0.509 ± 0.028 | 163 |
| `latest-pi-tc-wracc-high-20` | PI_TC · Thermal conductivity | WRAcc / alternative | Top 20%; ≥ 0.277747882 W/(m K) | 0.479 ± 0.006 | 216 |
| `latest-pi-tc-stca-high-10` | PI_TC · Thermal conductivity | STCA / primary | Top 10%; ≥ 0.3089501144 W/(m K) | 0.344 ± 0.012 | 163 |
| `latest-pi-tc-wracc-high-10` | PI_TC · Thermal conductivity | WRAcc / alternative | Top 10%; ≥ 0.3089501144 W/(m K) | 0.278 ± 0.047 | 180 |
| `latest-pi-ri-stca-high-30` | PI_RI · Refractive index | STCA / alternative | Top 30%; ≥ 1.5912610684 1 | 0.643 ± 0.016 | 300 |
| `latest-pi-ri-wracc-high-30` | PI_RI · Refractive index | WRAcc / primary | Top 30%; ≥ 1.5912610684 1 | 0.701 ± 0.009 | 417 |
| `latest-pi-ri-stca-high-20` | PI_RI · Refractive index | STCA / alternative | Top 20%; ≥ 1.63051903 1 | 0.595 ± 0.010 | 189 |
| `latest-pi-ri-wracc-high-20` | PI_RI · Refractive index | WRAcc / primary | Top 20%; ≥ 1.63051903 1 | 0.672 ± 0.011 | 296 |
| `latest-pi-ri-stca-high-10` | PI_RI · Refractive index | STCA / alternative | Top 10%; ≥ 1.6695841006 1 | 0.465 ± 0.003 | 189 |
| `latest-pi-ri-wracc-high-10` | PI_RI · Refractive index | WRAcc / primary | Top 10%; ≥ 1.6695841006 1 | 0.614 ± 0.026 | 171 |
| `latest-pi-rho-stca-high-30` | PI_RHO · Density | STCA / alternative | Top 30%; ≥ 1.222343047 g/cm3 | 0.582 ± 0.017 | 135 |
| `latest-pi-rho-wracc-high-30` | PI_RHO · Density | WRAcc / primary | Top 30%; ≥ 1.222343047 g/cm3 | 0.677 ± 0.003 | 408 |
| `latest-pi-rho-stca-high-20` | PI_RHO · Density | STCA / primary | Top 20%; ≥ 1.264285557 g/cm3 | 0.568 ± 0.012 | 135 |
| `latest-pi-rho-wracc-high-20` | PI_RHO · Density | WRAcc / alternative | Top 20%; ≥ 1.264285557 g/cm3 | 0.544 ± 0.001 | 366 |
| `latest-pi-rho-stca-high-10` | PI_RHO · Density | STCA / alternative | Top 10%; ≥ 1.308883696 g/cm3 | 0.522 ± 0.008 | 135 |
| `latest-pi-rho-wracc-high-10` | PI_RHO · Density | WRAcc / primary | Top 10%; ≥ 1.308883696 g/cm3 | 0.605 ± 0.002 | 172 |
| `latest-pi-cp-stca-high-30` | PI_CP · Specific heat | STCA / alternative | Top 30%; ≥ 3450.9014262 J/(kg K) | 0.627 ± 0.004 | 229 |
| `latest-pi-cp-wracc-high-30` | PI_CP · Specific heat | WRAcc / primary | Top 30%; ≥ 3450.9014262 J/(kg K) | 0.685 ± 0.008 | 466 |
| `latest-pi-cp-stca-high-20` | PI_CP · Specific heat | STCA / alternative | Top 20%; ≥ 3697.8346674 J/(kg K) | 0.553 ± 0.004 | 123 |
| `latest-pi-cp-wracc-high-20` | PI_CP · Specific heat | WRAcc / primary | Top 20%; ≥ 3697.8346674 J/(kg K) | 0.641 ± 0.015 | 271 |
| `latest-pi-cp-stca-high-10` | PI_CP · Specific heat | STCA / primary | Top 10%; ≥ 4069.3747128 J/(kg K) | 0.657 ± 0.021 | 109 |
| `latest-pi-cp-wracc-high-10` | PI_CP · Specific heat | WRAcc / alternative | Top 10%; ≥ 4069.3747128 J/(kg K) | 0.512 ± 0.010 | 234 |
| `latest-pi-dc-stca-high-30` | PI_DC · Dielectric constant | STCA / alternative | Top 30%; ≥ 3.0140665484 1 | 0.298 ± 0.020 | 480 |
| `latest-pi-dc-wracc-high-30` | PI_DC · Dielectric constant | WRAcc / primary | Top 30%; ≥ 3.0140665484 1 | 0.504 ± 0.015 | 355 |
| `latest-pi-dc-stca-high-20` | PI_DC · Dielectric constant | STCA / alternative | Top 20%; ≥ 3.1726934324 1 | 0.200 ± 0.032 | 480 |
| `latest-pi-dc-wracc-high-20` | PI_DC · Dielectric constant | WRAcc / primary | Top 20%; ≥ 3.1726934324 1 | 0.435 ± 0.009 | 300 |
| `latest-pi-dc-stca-high-10` | PI_DC · Dielectric constant | STCA / alternative | Top 10%; ≥ 3.8002543686 1 | 0.157 ± 0.006 | 55 |
| `latest-pi-dc-wracc-high-10` | PI_DC · Dielectric constant | WRAcc / primary | Top 10%; ≥ 3.8002543686 1 | 0.474 ± 0.019 | 158 |
| `latest-ad-tc-stca-high-30` | AD_TC · Thermal conductivity | STCA / alternative | Top 30%; ≥ 0.272 W/(m K) | 0.428 ± 0.017 | 1092 |
| `latest-ad-tc-wracc-high-30` | AD_TC · Thermal conductivity | WRAcc / primary | Top 30%; ≥ 0.272 W/(m K) | 0.581 ± 0.006 | 746 |
| `latest-ad-tc-stca-high-20` | AD_TC · Thermal conductivity | STCA / alternative | Top 20%; ≥ 0.307 W/(m K) | 0.364 ± 0.019 | 1092 |
| `latest-ad-tc-wracc-high-20` | AD_TC · Thermal conductivity | WRAcc / primary | Top 20%; ≥ 0.307 W/(m K) | 0.495 ± 0.003 | 580 |
| `latest-ad-tc-stca-high-10` | AD_TC · Thermal conductivity | STCA / alternative | Top 10%; ≥ 0.354 W/(m K) | 0.218 ± 0.023 | 1092 |
| `latest-ad-tc-wracc-high-10` | AD_TC · Thermal conductivity | WRAcc / primary | Top 10%; ≥ 0.354 W/(m K) | 0.252 ± 0.009 | 842 |
| `latest-ad-rho-stca-high-30` | AD_RHO · Density | STCA / primary | Top 30%; ≥ 1.1357978 g/cm3 | 0.584 ± 0.012 | 298 |
| `latest-ad-rho-wracc-high-30` | AD_RHO · Density | WRAcc / alternative | Top 30%; ≥ 1.1357978 g/cm3 | 0.576 ± 0.004 | 652 |
| `latest-ad-rho-stca-high-20` | AD_RHO · Density | STCA / primary | Top 20%; ≥ 1.1933408 g/cm3 | 0.583 ± 0.011 | 298 |
| `latest-ad-rho-wracc-high-20` | AD_RHO · Density | WRAcc / alternative | Top 20%; ≥ 1.1933408 g/cm3 | 0.483 ± 0.003 | 652 |
| `latest-ad-rho-stca-high-10` | AD_RHO · Density | STCA / primary | Top 10%; ≥ 1.2680314 g/cm3 | 0.605 ± 0.007 | 143 |
| `latest-ad-rho-wracc-high-10` | AD_RHO · Density | WRAcc / alternative | Top 10%; ≥ 1.2680314 g/cm3 | 0.561 ± 0.009 | 290 |
| `latest-ad-gap-stca-high-30` | AD_GAP · Isolated-monomer HOMO-LUMO gap | STCA / alternative | Top 30%; ≥ 11.973042956 eV | 0.616 ± 0.005 | 899 |
| `latest-ad-gap-wracc-high-30` | AD_GAP · Isolated-monomer HOMO-LUMO gap | WRAcc / primary | Top 30%; ≥ 11.973042956 eV | 0.766 ± 0.002 | 1086 |
| `latest-ad-gap-stca-high-20` | AD_GAP · Isolated-monomer HOMO-LUMO gap | STCA / alternative | Top 20%; ≥ 12.52710563 eV | 0.499 ± 0.035 | 899 |
| `latest-ad-gap-wracc-high-20` | AD_GAP · Isolated-monomer HOMO-LUMO gap | WRAcc / primary | Top 20%; ≥ 12.52710563 eV | 0.725 ± 0.001 | 848 |
| `latest-ad-gap-stca-high-10` | AD_GAP · Isolated-monomer HOMO-LUMO gap | STCA / primary | Top 10%; ≥ 12.902463866 eV | 0.460 ± 0.006 | 121 |
| `latest-ad-gap-wracc-high-10` | AD_GAP · Isolated-monomer HOMO-LUMO gap | WRAcc / alternative | Top 10%; ≥ 12.902463866 eV | 0.437 ± 0.001 | 848 |
| `latest-ad-dc-stca-high-30` | AD_DC · Dielectric constant | STCA / alternative | Top 30%; ≥ 2.7478344 1 | 0.269 ± 0.021 | 3 |
| `latest-ad-dc-wracc-high-30` | AD_DC · Dielectric constant | WRAcc / primary | Top 30%; ≥ 2.7478344 1 | 0.478 ± 0.014 | 301 |
| `latest-ad-dc-stca-high-20` | AD_DC · Dielectric constant | STCA / alternative | Top 20%; ≥ 2.961622 1 | 0.231 ± 0.057 | 2 |
| `latest-ad-dc-wracc-high-20` | AD_DC · Dielectric constant | WRAcc / primary | Top 20%; ≥ 2.961622 1 | 0.376 ± 0.024 | 273 |
| `latest-ad-dc-stca-high-10` | AD_DC · Dielectric constant | STCA / alternative | Top 10%; ≥ 3.331636600000001 1 | 0.211 ± 0.117 | 2 |
| `latest-ad-dc-wracc-high-10` | AD_DC · Dielectric constant | WRAcc / primary | Top 10%; ≥ 3.331636600000001 1 | 0.239 ± 0.021 | 189 |
| `latest-ad-ri-stca-high-30` | AD_RI · Refractive index | STCA / alternative | Top 30%; ≥ 1.5128804 1 | 0.588 ± 0.043 | 310 |
| `latest-ad-ri-wracc-high-30` | AD_RI · Refractive index | WRAcc / primary | Top 30%; ≥ 1.5128804 1 | 0.645 ± 0.002 | 267 |
| `latest-ad-ri-stca-high-20` | AD_RI · Refractive index | STCA / alternative | Top 20%; ≥ 1.5359912 1 | 0.485 ± 0.021 | 310 |
| `latest-ad-ri-wracc-high-20` | AD_RI · Refractive index | WRAcc / primary | Top 20%; ≥ 1.5359912 1 | 0.682 ± 0.016 | 169 |
| `latest-ad-ri-stca-high-10` | AD_RI · Refractive index | STCA / alternative | Top 10%; ≥ 1.5686904000000002 1 | 0.333 ± 0.023 | 281 |
| `latest-ad-ri-wracc-high-10` | AD_RI · Refractive index | WRAcc / primary | Top 10%; ≥ 1.5686904000000002 1 | 0.437 ± 0.006 | 169 |

Latest source evidence is in `evidence/latest_20261108/`. Its native model is available only for AD_GAP; the 72 exact exported conjunctions are directly usable frozen rules and are not reconstructed native STCA/WRAcc models. Fold models and fold constraints were not supplied.
