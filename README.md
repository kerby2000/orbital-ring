# OR-0 / OR-1 / OR-2 orbital-ring feasibility kernel

This repository is the initial traceable Python kernel for a polygonal,
discontinuous equatorial Earth orbital ring. It implements:

- **L0** closed-form orbital turning and large-N Earth-fixed physical-guide
  scaling;
- **L1** numerical planar two-body propagation between rotating Earth-fixed
  point nodes;
- rotor population, energy, passage-frequency, guide-occupancy, and mean
  reaction-force scaling;
- OR-1.1 Earth-fixed guide-frame kinematics that keep interaction time,
  inertial turn path, and physical guide length separate;
- an immutable OR-1.1-to-OR-2 `GuideDemand` adapter and invertible
  length/capability guide studies;
- **M0** Maxwell pressure/energy-density bounds and **M1** analytic
  quadrupole, dipole, ferromagnetic, permanent-magnet, superconducting-loop,
  conductive-loop, aperture, packing, coupling, and ripple/loss models;
- a source-backed material registry under `data/materials/`;
- strict unit-bearing YAML scenarios, machine-readable manifests, explicit
  parameter sweeps, and a reproducible Markdown report.

It does **not** provide a production magnet design, 3-D FEM, detailed
cryogenics/quench or REBCO AC loss, structural/thermal closure, a global
controller/optimizer, or a polished dashboard.

## Quick start

Python 3.11 or newer is required.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m pytest
.venv/Scripts/orbital-ring run scenarios/reference.yaml --output artifacts/reference-run
.venv/Scripts/orbital-ring report scenarios/reference.yaml --output artifacts/baseline
.venv/Scripts/orbital-ring or2-evidence scenarios/reference.yaml --output artifacts/generated/or-2
```

On POSIX shells, replace `.venv/Scripts/...` with `.venv/bin/...`.

Each `run` writes `result.json` plus `manifest.json`. The manifest contains the
scenario ID, complete canonical SI inputs, derived values, model/fidelity
version, source Git commit when available, UTC timestamp, SHA-256 configuration
hash, runtime library versions, numerical solver settings, and warnings. The
`artifact_commit` field remains null because a file cannot embed the hash of
the commit containing that same file. No required physical input receives a
silent default.

## Configuration

Physical YAML values must carry units. See
[`scenarios/reference.yaml`](scenarios/reference.yaml). The current L1 solver
accepts only an equatorial, prograde stream; unsupported geometry is rejected
instead of being approximated silently.

`transfer.node_stride` is a ballistic leg primitive: 1 targets the next node,
2 bypasses one intermediate node, and 3 bypasses two. Legacy
`transfer.skip_nodes` YAML is accepted with a manifest warning. Static failed
node routes are represented separately, so a local failure does not turn the
whole stream into a homogeneous stride-two ring.

Failure-route results also contain node transitions. The two guides bordering
a failed-node cluster use mixed incoming/outgoing strides; periodic stride-k
turns are never reported as those local guide requirements.

The public API intended for a later read-only application is small:

```python
from orbital_ring import evaluate_failure_route, evaluate_scenario, load_scenario

scenario = load_scenario("scenarios/reference.yaml")
result = evaluate_scenario(scenario)
print(result.ballistic.minimum_altitude_m)

failure = evaluate_failure_route(scenario, failed_nodes=[12, 13])
print(failure.bypass_legs[0].ballistic.node_stride)  # 3

from orbital_ring import build_guide_demand
from orbital_ring.magnetic_demand import solve_acceleration_for_guide_length

demand = build_guide_demand(scenario, result)
length_driven = solve_acceleration_for_guide_length(demand, 1000.0)
print(length_driven.required_lateral_acceleration_m_s2)
```

## Sweeps

[`sweeps/initial-one-at-a-time.yaml`](sweeps/initial-one-at-a-time.yaml)
contains all initially requested axes and values. Its `active_dimensions` list
explicitly selects what runs. `one_at_a_time` evaluates a baseline and varies
one parameter per design point, avoiding the 2,200-point Cartesian product.

```bash
orbital-ring sweep sweeps/node-count-only.yaml --output artifacts/node-sweep
orbital-ring evidence scenarios/reference.yaml --output ci-evidence/or-1.1
orbital-ring or2-evidence scenarios/reference.yaml --output ci-evidence/or-2
```

CSV, Parquet, a complete JSON result set, and a sweep manifest are written.
A configured Cartesian design is refused unless `--allow-cartesian` is passed.
The `evidence` command writes global force closure, physical-guide convergence,
finite-node L1, free-flight bypass, mixed node-transition, and rotor-element
scaling tables.

The `or2-evidence` command writes bounded magnetic-demand, specific-moment,
rotor-concept, Maxwell-pressure, aperture/field-energy, ripple/loss,
conductive-loop, packing/coupling, node-count, and source-registry tables. Its
1000-g0 cases are regression points; guide length and magnetic capability are
otherwise invertible.

## Repository layout

```text
.
├── README.md
├── MODEL.md
├── ASSUMPTIONS.md
├── MAGNETIC_SOURCES.md
├── VALIDATION.md
├── pyproject.toml
├── scenarios/
├── sweeps/
├── data/materials/
├── src/orbital_ring/
│   ├── analysis.py
│   ├── ballistic.py
│   ├── cli.py
│   ├── config.py
│   ├── constants.py
│   ├── geometry.py
│   ├── guide.py
│   ├── magnetic_demand.py
│   ├── magnetic_field.py
│   ├── magnetic_geometry.py
│   ├── magnetic_losses.py
│   ├── magnetic_results.py
│   ├── magnetic_rotors.py
│   ├── materials.py
│   ├── manifest.py
│   ├── network.py
│   ├── orbit.py
│   ├── report.py
│   ├── results.py
│   ├── rotor.py
│   ├── sweep.py
│   ├── evidence.py
│   ├── or2_evidence.py
│   └── units.py
└── tests/
```

See [MODEL.md](MODEL.md) for equations and [ASSUMPTIONS.md](ASSUMPTIONS.md)
for the boundary of the model. [GENERATED_ARTIFACTS.md](GENERATED_ARTIFACTS.md)
defines what evidence is tracked versus produced by CI,
[OR2_INTERFACES.md](OR2_INTERFACES.md) records the implemented layer boundary,
and [MAGNETIC_SOURCES.md](MAGNETIC_SOURCES.md) explains source validity.
