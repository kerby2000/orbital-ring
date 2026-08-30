# Validation strategy

## Automated checks

The test suite covers:

1. Direct evaluation of every requested L0 equation.
2. The 500 km, 12 km/s, 1000 \(g_0\) reference values with documented
   tolerances.
3. L1's independent circular-orbit limit: at \(v=v_{orb}\), the numerical
   trajectory stays at constant radius and reaches the rotating target after
   \(t=\Delta\lambda/(v_{orb}/r-\omega_E)\).
4. Direct, one-node-bypass, and two-node-bypass solutions (node strides 1, 2,
   and 3), including endpoint speed and target position error.
5. Earth-intersection and configurable minimum-safe-altitude flags.
6. Exact rotor force consistency between momentum flow and the vector sum of
   simultaneous guide forces.
7. Strict rejection of missing parameters and unitless dimensional inputs.
8. CSV/Parquet/JSON/manifest production for a bounded L0 sweep.
9. Static topology tests proving that one or two adjacent failures create only
   one local bypass leg while unaffected legs retain stride 1.
10. Global force closure for N = 48, 96, 192, 480, 960, and 1920, including
    monotonic finite-N convergence to continuous support force.
11. Runtime and numerical provenance fields in run and sweep manifests.
12. Earth-fixed guide-frame quadrature, including the 96-node 573.86 m
    reference and separation from the 598.87 m inertial turn path.
13. Physical guide-length convergence to 55.093079 km for N = 48 through 1920.
14. Mixed stride 1↔2 and 1↔3 transition angles and guide lengths at both
    endpoints of one- and two-failure bypasses.
15. Exact length-driven/capability-driven guide inversion and node impulse
    closure through `GuideDemand`.
16. Synthetic `F=mu G`, `a=(mu/m)G`, and fixed-specific-moment mass
    cancellation.
17. Quadrupole pole-tip field and closed-form aperture energy against an
    independent numerical area integral.
18. Maxwell pressure/energy-density identity.
19. Source-backed ferromagnet/permanent-magnet moments and persistent-loop
    `mu=NIA`, including strict rejection of unsupported REBCO current margins.
20. Sinusoidal R-L steady state, ripple frequency, classical eddy scaling,
    skin-depth/source-domain flags, packing overlap, and point-dipole neighbor
    formulas.
21. Small-element studies showing constant gradient, aperture-floor behavior,
    worsening packing, and increasing coupling.

Run:

```bash
python -m pytest
```

## Reference tolerances

The requirements quote rounded targets. Tests use:

| Quantity | Target | Test tolerance |
|---|---:|---:|
| Circular velocity | 7.62 km/s | ±0.01 km/s |
| Magnetic turn over inertial-period circuit | 3.75193436 rad | ±1×10⁻⁸ rad |
| Magnetic turn over Earth-relative circuit | 3.91541644 rad | ±1×10⁻⁸ rad |
| Magnetic curvature radius | 14.7 km | ±0.1 km |
| Total L0 guide length | 55 km | ±1 km |
| 96-node physical Earth-fixed guide | 573.86 m | ±0.1 m |
| Mixed stride 1↔2 transition | 0.06117075 rad | ±2×10⁻⁸ rad |
| Mixed stride 1↔3 transition | 0.08154744 rad | ±2×10⁻⁸ rad |

The constants in the supplied scenario produce more digits than these rounded
acceptance values; generated results retain full machine precision.

## Numerical convergence checks

The default DOP853 integration uses relative tolerance \(2\times10^{-10}\),
absolute state tolerance \(10^{-7}\), and at least 80 nominal integration
steps per transfer. A shooting solution is rejected if its terminal position
error exceeds 0.25 m. These are numerical controls, not physical uncertainty
bounds.

## Remaining validation gaps

- No independent high-fidelity propagator is included in OR-1.
- Hyperbolic and Earth-intersecting branches need a broader regression corpus.
- Finite-duration guide dynamics have only the momentum-vector identity check;
  guide-frame kinematics are not propagated through a gravity or field model.
- Bypass stream transients and phase allocation require a control model beyond
  the static topology now included.
- M0/M1 magnetic models need comparison with 2-D/3-D field solvers and measured
  force data over the relevant gradient, offset, temperature, and frequency
  domains.
- REBCO in-field current margin and external-field AC loss are intentionally
  unsupported with the current scalar source data.
- Magnetic, structural, thermal, orientation/control, and collective-stream
  models are not yet coupled.
