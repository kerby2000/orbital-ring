# OR-2 magnetic source registry

The machine-readable registry is `data/materials/registry.json`. Every stored
non-fundamental property includes its value, unit, temperature, field
condition, source organization/title/URL, access date, and validity note.
Study choices such as utilization factors, navigation margins, ripple
amplitudes, and separation margins are not material facts and are kept in the
OR-2 evidence generator instead.

## Registered datasets

| Identifier | Use | Primary source and boundary |
| --- | --- | --- |
| `vacoflux_50` | Saturated Fe-Co moment and conductive-loss benchmark | VAC VACOFLUX 50 product information: 2.30 T saturation polarization, 8120 kg/m3, 0.42 micro-ohm metre. Saturation remains a modeled upper bound with explicit utilization. |
| `vacodym_902_tp` | NdFeB permanent-dipole benchmark | VAC current VACODYM product information: minimum 1.40 T remanence and 1190 kA/m intrinsic coercivity at room temperature. The family guidance to consult VAC above 150 degC is a warning threshold, not a guaranteed grade maximum. |
| `tdk_n87` | High-resistivity ferrite comparison | TDK N87 sheet: 0.49 T at 25 degC, H=1200 A/m and 10 kHz; 10 ohm metre; preferred 25-500 kHz range. The stated flux density is not silently generalized to other temperatures/frequencies. |
| `superpower_ap_4mm` | Persistent REBCO loop conductor benchmark | SuperPower 4-mm AP tape options and 120-160 A critical current at 77 K self-field. OR-2 refuses to infer an in-field critical current from this scalar range. |
| `hastelloy_c276` | REBCO substrate mass estimate | Haynes C-276 room-temperature density. |
| `copper_c10810` | Stabilizer and R-L loop benchmark | Copper Development Association room-temperature density/resistivity. No cryogenic resistivity is inferred. |
| `aluminum_1050_o` | Alternate R-L loop benchmark | NIST wrought-aluminum compilation at 20 degC. |
| `mqxf_benchmark` | External accelerator-magnet scale | CERN/US-LARP MQXF: 150-mm aperture, 132.6 T/m nominal gradient, 11.4 T peak conductor field at 1.9 K. This is not evidence that a comparable orbital guide has acceptable mass, energy, protection, or cost. |

## Explicit data limitations

- SuperPower publishes in-field curves by temperature and orientation, but the
  current OR-2 registry contains only the tabulated 77 K self-field range.
  Requested in-field operating points are therefore reported as unsupported,
  not extrapolated.
- VACODYM demagnetization depends on geometry, load line, temperature, and
  field orientation. The M1 permanent-magnet model reports only a simple
  coercivity field-scale comparison.
- N87 published core-loss points are not extrapolated. OR-2 uses only the
  classical eddy-current expression as a separately labeled comparison and
  checks its thin-section/skin-depth domain.
- Material data do not specify manufacturable rotor construction, fatigue,
  containment, radiation tolerance, joining, or thermal rejection.
