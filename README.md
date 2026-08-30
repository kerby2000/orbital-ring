# OR-0 / OR-1 orbital-ring simulation kernel

This repository is the initial traceable Python kernel for a polygonal,
discontinuous equatorial Earth orbital ring. It implements only:

- **L0** closed-form orbital and magnetic turning/guide-length scaling;
- **L1** numerical planar two-body propagation between rotating Earth-fixed
  point nodes;
- rotor population, energy, passage-frequency, guide-occupancy, and mean
  reaction-force scaling;
- strict unit-bearing YAML scenarios, machine-readable manifests, explicit
  parameter sweeps, and a reproducible Markdown report.

It does **not** design magnets or model heat, control, optimization, flexible
structures, finite node geometry, or a dashboard.

## Quick start

Python 3.11 or newer is required.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m pytest
.venv/Scripts/orbital-ring run scenarios/reference.yaml --output artifacts/reference-run
.venv/Scripts/orbital-ring report scenarios/reference.yaml --output artifacts/baseline
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

The public API intended for a later read-only application is small:

```python
from orbital_ring import evaluate_failure_route, evaluate_scenario, load_scenario

scenario = load_scenario("scenarios/reference.yaml")
result = evaluate_scenario(scenario)
print(result.ballistic.minimum_altitude_m)

failure = evaluate_failure_route(scenario, failed_nodes=[12, 13])
print(failure.bypass_legs[0].ballistic.node_stride)  # 3
```

## Sweeps

[`sweeps/initial-one-at-a-time.yaml`](sweeps/initial-one-at-a-time.yaml)
contains all initially requested axes and values. Its `active_dimensions` list
explicitly selects what runs. `one_at_a_time` evaluates a baseline and varies
one parameter per design point, avoiding the 2,200-point Cartesian product.

```bash
orbital-ring sweep sweeps/node-count-only.yaml --output artifacts/node-sweep
orbital-ring evidence scenarios/reference.yaml --output ci-evidence/or-1.1
```

CSV, Parquet, a complete JSON result set, and a sweep manifest are written.
A configured Cartesian design is refused unless `--allow-cartesian` is passed.
The `evidence` command writes global force closure, finite-node L1, local
failure bypass, and rotor-element scaling tables.

## Repository layout

```text
.
├── README.md
├── MODEL.md
├── ASSUMPTIONS.md
├── VALIDATION.md
├── pyproject.toml
├── scenarios/
├── sweeps/
├── src/orbital_ring/
│   ├── analysis.py
│   ├── ballistic.py
│   ├── cli.py
│   ├── config.py
│   ├── constants.py
│   ├── geometry.py
│   ├── manifest.py
│   ├── network.py
│   ├── orbit.py
│   ├── report.py
│   ├── results.py
│   ├── rotor.py
│   ├── sweep.py
│   ├── evidence.py
│   └── units.py
└── tests/
```

See [MODEL.md](MODEL.md) for equations and [ASSUMPTIONS.md](ASSUMPTIONS.md)
for the boundary of the model. [GENERATED_ARTIFACTS.md](GENERATED_ARTIFACTS.md)
defines what evidence is tracked versus produced by CI, and
[OR2_INTERFACES.md](OR2_INTERFACES.md) records the proposed extension boundaries.
