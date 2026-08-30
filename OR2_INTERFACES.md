# Implemented OR-2 extension interfaces

OR-2 is additive. It does not modify the L0/L1 orbital equations, L1 shooting
solver, Earth-fixed guide quadrature, or failure-route topology.

## `GuideDemand`

`orbital_ring.magnetic_demand.build_guide_demand()` is the sole normal-route
adapter from an accepted OR-1.1 `SimulationResult`. Its frozen record carries:

- scenario/configuration and transition identity;
- local incoming/outgoing inertial velocity vectors;
- guide tangential velocity, turn angle, delta-v, net impulse, and integrated
  lateral impulse;
- element mass, passage frequency, node mean reaction, and guide spacing;
- guide-relative entry/exit/representative speeds;
- the legacy acceleration, physical guide length, and interaction time;
- source model/commit traceability.

Magnetic modules consume this record or explicit magnetic/material inputs.
They do not call `evaluate_scenario`, the ballistic solver, or orbital
closed-form functions.

## Invertible guide study

`solve_acceleration_for_guide_length()` provides length-driven demand.
`solve_guide_length_for_acceleration()` and
`solve_guide_length_for_force()` provide capability-driven results. All return
the same immutable result schema with impulse-based node-force closure.

## Independent magnetic modules

- `magnetic_field.py`: M0 pressure, M1 quadrupole, generic aligned dipole;
- `magnetic_rotors.py`: Fe-Co/ferrite saturation surrogate, NdFeB permanent
  dipole, and persistent-current REBCO loop;
- `magnetic_losses.py`: longitudinal ripple, skin depth, classical thin-section
  eddy comparison, and conductive R-L loop;
- `magnetic_geometry.py`: sphere/cylinder/loop envelopes, aperture floor,
  stream packing, and point-dipole neighbor coupling;
- `materials.py`: validated access to `data/materials/registry.json`;
- `or2_evidence.py`: bounded study orchestration and reporting only.

Equations remain in importable physics modules; CLI/report code contains no
independent force law.

## Deferred interfaces for OR-3

OR-3 should add field-map and force-map protocols able to replace the ideal
quadrupole without changing `GuideDemand`, followed by material curves,
thermal/loss state, structural loads, finite guide ends, and a local
orientation/navigation controller. Global optimization should wait until
these component models have validated domains.
