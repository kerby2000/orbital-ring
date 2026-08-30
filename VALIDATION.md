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

Run:

```bash
python -m pytest
```

## Reference tolerances

The requirements quote rounded targets. Tests use:

| Quantity | Target | Test tolerance |
|---|---:|---:|
| Circular velocity | 7.62 km/s | ±0.01 km/s |
| L0 magnetic turning | 3.75 rad | ±0.02 rad |
| Magnetic curvature radius | 14.7 km | ±0.1 km |
| Total L0 guide length | 55 km | ±1 km |

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
  they are not propagated through a field model.
- Bypass stream periodicity and phase allocation require an explicit network
  topology model before engineering interpretation.
