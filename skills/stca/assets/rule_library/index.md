# STCA rule and prompt library

77 frozen rules; each includes exact constraints and English/Chinese generation prompts. Version 0.1.0.

Read catalog.json for machine-readable titles, physical units and resource paths. Read individual constraints only when selected.

| Rule ID | Target | Range |
|---|---|---|
| `paper-tg-high-30` | STCA paper · Glass-transition temperature | Top 30% |
| `paper-tg-high-20` | STCA paper · Glass-transition temperature | Top 20% |
| `paper-tg-high-10` | STCA paper · Glass-transition temperature | Top 10% |
| `paper-ec-low-20` | STCA paper · Electrical conductivity | Bottom 20% |
| `paper-ec-low-15` | STCA paper · Electrical conductivity | Bottom 15% |
| `paper-ec-low-10` | STCA paper · Electrical conductivity | Bottom 10% |
| `paper-ec-low-5` | STCA paper · Electrical conductivity | Bottom 5% |
| `paper-ec-high-20` | STCA paper · Electrical conductivity | Top 20% |
| `paper-ec-high-15` | STCA paper · Electrical conductivity | Top 15% |
| `paper-ec-high-10` | STCA paper · Electrical conductivity | Top 10% |
| `paper-ec-high-5` | STCA paper · Electrical conductivity | Top 5% |
| `gas-co2-high-10` | GAS_CO2 · CO2 permeability | Top 10% |
| `gas-co2-high-15` | GAS_CO2 · CO2 permeability | Top 15% |
| `gas-co2-high-20` | GAS_CO2 · CO2 permeability | Top 20% |
| `gas-co2-high-25` | GAS_CO2 · CO2 permeability | Top 25% |
| `gas-co2-high-30` | GAS_CO2 · CO2 permeability | Top 30% |
| `gas-o2-high-10` | GAS_O2 · O2 permeability | Top 10% |
| `gas-o2-high-15` | GAS_O2 · O2 permeability | Top 15% |
| `gas-o2-high-20` | GAS_O2 · O2 permeability | Top 20% |
| `gas-o2-high-25` | GAS_O2 · O2 permeability | Top 25% |
| `gas-o2-high-30` | GAS_O2 · O2 permeability | Top 30% |
| `radonpy-tc-high-10` | PI_TC · Thermal conductivity | Top 10% |
| `radonpy-tc-high-15` | PI_TC · Thermal conductivity | Top 15% |
| `radonpy-tc-high-20` | PI_TC · Thermal conductivity | Top 20% |
| `radonpy-tc-high-25` | PI_TC · Thermal conductivity | Top 25% |
| `radonpy-tc-high-30` | PI_TC · Thermal conductivity | Top 30% |
| `radonpy-ri-high-10` | PI_RI · Refractive index | Top 10% |
| `radonpy-ri-high-15` | PI_RI · Refractive index | Top 15% |
| `radonpy-ri-high-20` | PI_RI · Refractive index | Top 20% |
| `radonpy-ri-high-25` | PI_RI · Refractive index | Top 25% |
| `radonpy-ri-high-30` | PI_RI · Refractive index | Top 30% |
| `radonpy-density-high-10` | PI_RHO · Density | Top 10% |
| `radonpy-density-high-15` | PI_RHO · Density | Top 15% |
| `radonpy-density-high-20` | PI_RHO · Density | Top 20% |
| `radonpy-density-high-25` | PI_RHO · Density | Top 25% |
| `radonpy-density-high-30` | PI_RHO · Density | Top 30% |
| `radonpy-cp-high-10` | PI_CP · Specific heat | Top 10% |
| `radonpy-cp-high-15` | PI_CP · Specific heat | Top 15% |
| `radonpy-cp-high-20` | PI_CP · Specific heat | Top 20% |
| `radonpy-cp-high-25` | PI_CP · Specific heat | Top 25% |
| `radonpy-cp-high-30` | PI_CP · Specific heat | Top 30% |
| `radonpy-dc-high-10` | PI_DC · Dielectric constant | Top 10% |
| `radonpy-dc-high-15` | PI_DC · Dielectric constant | Top 15% |
| `radonpy-dc-high-20` | PI_DC · Dielectric constant | Top 20% |
| `radonpy-dc-high-25` | PI_DC · Dielectric constant | Top 25% |
| `radonpy-dc-high-30` | PI_DC · Dielectric constant | Top 30% |
| `adept-tc-high-10` | AD_TC · Thermal conductivity | Top 10% |
| `adept-tc-high-15` | AD_TC · Thermal conductivity | Top 15% |
| `adept-tc-high-20` | AD_TC · Thermal conductivity | Top 20% |
| `adept-tc-high-25` | AD_TC · Thermal conductivity | Top 25% |
| `adept-tc-high-30` | AD_TC · Thermal conductivity | Top 30% |
| `adept-density-high-10` | AD_RHO · Density | Top 10% |
| `adept-density-high-15` | AD_RHO · Density | Top 15% |
| `adept-density-high-20` | AD_RHO · Density | Top 20% |
| `adept-density-high-25` | AD_RHO · Density | Top 25% |
| `adept-density-high-30` | AD_RHO · Density | Top 30% |
| `adept-gap-high-10` | AD_GAP · Isolated-monomer HOMO-LUMO gap | Top 10% |
| `adept-gap-high-15` | AD_GAP · Isolated-monomer HOMO-LUMO gap | Top 15% |
| `adept-gap-high-20` | AD_GAP · Isolated-monomer HOMO-LUMO gap | Top 20% |
| `adept-gap-high-25` | AD_GAP · Isolated-monomer HOMO-LUMO gap | Top 25% |
| `adept-gap-high-30` | AD_GAP · Isolated-monomer HOMO-LUMO gap | Top 30% |
| `adept-dc-high-10` | AD_DC · Dielectric constant | Top 10% |
| `adept-dc-high-15` | AD_DC · Dielectric constant | Top 15% |
| `adept-dc-high-20` | AD_DC · Dielectric constant | Top 20% |
| `adept-dc-high-25` | AD_DC · Dielectric constant | Top 25% |
| `adept-dc-high-30` | AD_DC · Dielectric constant | Top 30% |
| `adept-ri-high-10` | AD_RI · Refractive index | Top 10% |
| `adept-ri-high-15` | AD_RI · Refractive index | Top 15% |
| `adept-ri-high-20` | AD_RI · Refractive index | Top 20% |
| `adept-ri-high-25` | AD_RI · Refractive index | Top 25% |
| `adept-ri-high-30` | AD_RI · Refractive index | Top 30% |
| `adept-tg-high-10` | AD_TG · Glass-transition temperature | Top 10% |
| `adept-tg-high-15` | AD_TG · Glass-transition temperature | Top 15% |
| `adept-tg-high-20` | AD_TG · Glass-transition temperature | Top 20% |
| `adept-tg-high-25` | AD_TG · Glass-transition temperature | Top 25% |
| `adept-tg-high-30` | AD_TG · Glass-transition temperature | Top 30% |
| `adept-gap-author-high-10` | AD_GAP · Isolated-monomer HOMO-LUMO gap | Top 10% |
