# STCA rule and prompt library

Choose a source, property and percentage. Each exact rule is an AND conjunction; recommended and alternative methods remain separate.

Version 0.1.0. 83 catalog results: 11 STCA paper rules and 72 current open-data method results. There are 82 applicable rules and one unavailable STCA result (RadonPy dielectric constant, Top 20%); its WRAcc alternative is available.

Current open-data rules preserve original polymer connection graphs and prepare each percentage independently. Physical boundaries describe the training objective; matching a rule does not measure a candidate's property.

| Rule ID | Source / property | Method | Percentage / boundary | Role |
|---|---|---|---|---|
| `paper-tg-high-30` | STCA paper / Glass-transition temperature | STCA | Top 30%; >= 204 degC | paper rule |
| `paper-tg-high-20` | STCA paper / Glass-transition temperature | STCA | Top 20%; >= 238 degC | paper rule |
| `paper-tg-high-10` | STCA paper / Glass-transition temperature | STCA | Top 10%; >= 275 degC | paper rule |
| `paper-ec-low-20` | STCA paper / Electrical conductivity | STCA | Bottom 20%; <= 1.689999982e-13 S/cm | paper rule |
| `paper-ec-low-15` | STCA paper / Electrical conductivity | STCA | Bottom 15%; <= 2.243078228e-14 S/cm | paper rule |
| `paper-ec-low-10` | STCA paper / Electrical conductivity | STCA | Bottom 10%; <= 1.899999996e-15 S/cm | paper rule |
| `paper-ec-low-5` | STCA paper / Electrical conductivity | STCA | Bottom 5%; <= 1.048808854e-16 S/cm | paper rule |
| `paper-ec-high-20` | STCA paper / Electrical conductivity | STCA | Top 20%; >= 5.400000002e-05 S/cm | paper rule |
| `paper-ec-high-15` | STCA paper / Electrical conductivity | STCA | Top 15%; >= 0.0003411378021 S/cm | paper rule |
| `paper-ec-high-10` | STCA paper / Electrical conductivity | STCA | Top 10%; >= 0.004199999996 S/cm | paper rule |
| `paper-ec-high-5` | STCA paper / Electrical conductivity | STCA | Top 5%; >= 0.0890772137 S/cm | paper rule |
| `current-gas-co2-stca-high-10` | GAS_CO2 / CO2 permeability | STCA | Top 10%; >= 7140 Barrer | alternative |
| `current-gas-co2-wracc-high-10` | GAS_CO2 / CO2 permeability | WRAcc | Top 10%; >= 7140 Barrer | primary |
| `current-gas-co2-stca-high-20` | GAS_CO2 / CO2 permeability | STCA | Top 20%; >= 2390 Barrer | alternative |
| `current-gas-co2-wracc-high-20` | GAS_CO2 / CO2 permeability | WRAcc | Top 20%; >= 2390 Barrer | primary |
| `current-gas-co2-stca-high-30` | GAS_CO2 / CO2 permeability | STCA | Top 30%; >= 634.2105263 Barrer | alternative |
| `current-gas-co2-wracc-high-30` | GAS_CO2 / CO2 permeability | WRAcc | Top 30%; >= 634.2105263 Barrer | primary |
| `current-gas-o2-stca-high-10` | GAS_O2 / O2 permeability | STCA | Top 10%; >= 1339.402852 Barrer | alternative |
| `current-gas-o2-wracc-high-10` | GAS_O2 / O2 permeability | WRAcc | Top 10%; >= 1339.402852 Barrer | primary |
| `current-gas-o2-stca-high-20` | GAS_O2 / O2 permeability | STCA | Top 20%; >= 439.3983569 Barrer | alternative |
| `current-gas-o2-wracc-high-20` | GAS_O2 / O2 permeability | WRAcc | Top 20%; >= 439.3983569 Barrer | primary |
| `current-gas-o2-stca-high-30` | GAS_O2 / O2 permeability | STCA | Top 30%; >= 76.3997389 Barrer | alternative |
| `current-gas-o2-wracc-high-30` | GAS_O2 / O2 permeability | WRAcc | Top 30%; >= 76.3997389 Barrer | primary |
| `current-pi-tc-stca-high-10` | PI_TC / Thermal conductivity | STCA | Top 10%; >= 0.3098994358 W/(m K) | alternative |
| `current-pi-tc-wracc-high-10` | PI_TC / Thermal conductivity | WRAcc | Top 10%; >= 0.3098994358 W/(m K) | primary |
| `current-pi-tc-stca-high-20` | PI_TC / Thermal conductivity | STCA | Top 20%; >= 0.277747882 W/(m K) | alternative |
| `current-pi-tc-wracc-high-20` | PI_TC / Thermal conductivity | WRAcc | Top 20%; >= 0.277747882 W/(m K) | primary |
| `current-pi-tc-stca-high-30` | PI_TC / Thermal conductivity | STCA | Top 30%; >= 0.2586913575 W/(m K) | alternative |
| `current-pi-tc-wracc-high-30` | PI_TC / Thermal conductivity | WRAcc | Top 30%; >= 0.2586913575 W/(m K) | primary |
| `current-pi-ri-stca-high-10` | PI_RI / Refractive index | STCA | Top 10%; >= 1.671039499 1 | alternative |
| `current-pi-ri-wracc-high-10` | PI_RI / Refractive index | WRAcc | Top 10%; >= 1.671039499 1 | primary |
| `current-pi-ri-stca-high-20` | PI_RI / Refractive index | STCA | Top 20%; >= 1.631549914 1 | alternative |
| `current-pi-ri-wracc-high-20` | PI_RI / Refractive index | WRAcc | Top 20%; >= 1.631549914 1 | primary |
| `current-pi-ri-stca-high-30` | PI_RI / Refractive index | STCA | Top 30%; >= 1.591863746 1 | alternative |
| `current-pi-ri-wracc-high-30` | PI_RI / Refractive index | WRAcc | Top 30%; >= 1.591863746 1 | primary |
| `current-pi-rho-stca-high-10` | PI_RHO / Density | STCA | Top 10%; >= 1.307512211 g/cm3 | alternative |
| `current-pi-rho-wracc-high-10` | PI_RHO / Density | WRAcc | Top 10%; >= 1.307512211 g/cm3 | primary |
| `current-pi-rho-stca-high-20` | PI_RHO / Density | STCA | Top 20%; >= 1.265451171 g/cm3 | alternative |
| `current-pi-rho-wracc-high-20` | PI_RHO / Density | WRAcc | Top 20%; >= 1.265451171 g/cm3 | primary |
| `current-pi-rho-stca-high-30` | PI_RHO / Density | STCA | Top 30%; >= 1.222080875 g/cm3 | alternative |
| `current-pi-rho-wracc-high-30` | PI_RHO / Density | WRAcc | Top 30%; >= 1.222080875 g/cm3 | primary |
| `current-pi-cp-stca-high-10` | PI_CP / Specific heat | STCA | Top 10%; >= 4095.394701 J/(kg K) | primary |
| `current-pi-cp-wracc-high-10` | PI_CP / Specific heat | WRAcc | Top 10%; >= 4095.394701 J/(kg K) | alternative |
| `current-pi-cp-stca-high-20` | PI_CP / Specific heat | STCA | Top 20%; >= 3708.270525 J/(kg K) | alternative |
| `current-pi-cp-wracc-high-20` | PI_CP / Specific heat | WRAcc | Top 20%; >= 3708.270525 J/(kg K) | primary |
| `current-pi-cp-stca-high-30` | PI_CP / Specific heat | STCA | Top 30%; >= 3458.801419 J/(kg K) | alternative |
| `current-pi-cp-wracc-high-30` | PI_CP / Specific heat | WRAcc | Top 30%; >= 3458.801419 J/(kg K) | primary |
| `current-pi-dc-stca-high-10` | PI_DC / Dielectric constant | STCA | Top 10%; >= 3.672201564 1 | alternative |
| `current-pi-dc-wracc-high-10` | PI_DC / Dielectric constant | WRAcc | Top 10%; >= 3.672201564 1 | primary |
| `current-pi-dc-stca-high-20` | PI_DC / Dielectric constant | STCA | Top 20%; >= 3.160277715 1 | no valid rule; generation unavailable |
| `current-pi-dc-wracc-high-20` | PI_DC / Dielectric constant | WRAcc | Top 20%; >= 3.160277715 1 | primary |
| `current-pi-dc-stca-high-30` | PI_DC / Dielectric constant | STCA | Top 30%; >= 3.010841517 1 | primary |
| `current-pi-dc-wracc-high-30` | PI_DC / Dielectric constant | WRAcc | Top 30%; >= 3.010841517 1 | alternative |
| `current-ad-tc-stca-high-10` | AD_TC / Thermal conductivity | STCA | Top 10%; >= 0.356 W/(m K) | alternative |
| `current-ad-tc-wracc-high-10` | AD_TC / Thermal conductivity | WRAcc | Top 10%; >= 0.356 W/(m K) | primary |
| `current-ad-tc-stca-high-20` | AD_TC / Thermal conductivity | STCA | Top 20%; >= 0.308 W/(m K) | primary |
| `current-ad-tc-wracc-high-20` | AD_TC / Thermal conductivity | WRAcc | Top 20%; >= 0.308 W/(m K) | alternative |
| `current-ad-tc-stca-high-30` | AD_TC / Thermal conductivity | STCA | Top 30%; >= 0.272 W/(m K) | alternative |
| `current-ad-tc-wracc-high-30` | AD_TC / Thermal conductivity | WRAcc | Top 30%; >= 0.272 W/(m K) | primary |
| `current-ad-rho-stca-high-10` | AD_RHO / Density | STCA | Top 10%; >= 1.2675096 g/cm3 | primary |
| `current-ad-rho-wracc-high-10` | AD_RHO / Density | WRAcc | Top 10%; >= 1.2675096 g/cm3 | alternative |
| `current-ad-rho-stca-high-20` | AD_RHO / Density | STCA | Top 20%; >= 1.1927404 g/cm3 | alternative |
| `current-ad-rho-wracc-high-20` | AD_RHO / Density | WRAcc | Top 20%; >= 1.1927404 g/cm3 | primary |
| `current-ad-rho-stca-high-30` | AD_RHO / Density | STCA | Top 30%; >= 1.13529403 g/cm3 | primary |
| `current-ad-rho-wracc-high-30` | AD_RHO / Density | WRAcc | Top 30%; >= 1.13529403 g/cm3 | alternative |
| `current-ad-gap-stca-high-10` | AD_GAP / H-capped isolated-monomer HOMO–LUMO gap | STCA | Top 10%; >= 12.94009876 eV | alternative |
| `current-ad-gap-wracc-high-10` | AD_GAP / H-capped isolated-monomer HOMO–LUMO gap | WRAcc | Top 10%; >= 12.94009876 eV | primary |
| `current-ad-gap-stca-high-20` | AD_GAP / H-capped isolated-monomer HOMO–LUMO gap | STCA | Top 20%; >= 12.57122579 eV | alternative |
| `current-ad-gap-wracc-high-20` | AD_GAP / H-capped isolated-monomer HOMO–LUMO gap | WRAcc | Top 20%; >= 12.57122579 eV | primary |
| `current-ad-gap-stca-high-30` | AD_GAP / H-capped isolated-monomer HOMO–LUMO gap | STCA | Top 30%; >= 12.0108438 eV | alternative |
| `current-ad-gap-wracc-high-30` | AD_GAP / H-capped isolated-monomer HOMO–LUMO gap | WRAcc | Top 30%; >= 12.0108438 eV | primary |
| `current-ad-dc-stca-high-10` | AD_DC / Dielectric constant | STCA | Top 10%; >= 3.35917 1 | alternative |
| `current-ad-dc-wracc-high-10` | AD_DC / Dielectric constant | WRAcc | Top 10%; >= 3.35917 1 | primary |
| `current-ad-dc-stca-high-20` | AD_DC / Dielectric constant | STCA | Top 20%; >= 2.9605954 1 | alternative |
| `current-ad-dc-wracc-high-20` | AD_DC / Dielectric constant | WRAcc | Top 20%; >= 2.9605954 1 | primary |
| `current-ad-dc-stca-high-30` | AD_DC / Dielectric constant | STCA | Top 30%; >= 2.7474674 1 | alternative |
| `current-ad-dc-wracc-high-30` | AD_DC / Dielectric constant | WRAcc | Top 30%; >= 2.7474674 1 | primary |
| `current-ad-ri-stca-high-10` | AD_RI / Refractive index | STCA | Top 10%; >= 1.5689754 1 | alternative |
| `current-ad-ri-wracc-high-10` | AD_RI / Refractive index | WRAcc | Top 10%; >= 1.5689754 1 | primary |
| `current-ad-ri-stca-high-20` | AD_RI / Refractive index | STCA | Top 20%; >= 1.5372859 1 | alternative |
| `current-ad-ri-wracc-high-20` | AD_RI / Refractive index | WRAcc | Top 20%; >= 1.5372859 1 | primary |
| `current-ad-ri-stca-high-30` | AD_RI / Refractive index | STCA | Top 30%; >= 1.5129934 1 | alternative |
| `current-ad-ri-wracc-high-30` | AD_RI / Refractive index | WRAcc | Top 30%; >= 1.5129934 1 | primary |
