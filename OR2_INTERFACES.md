# Proposed OR-2 extension interfaces

OR-2 should add magnet and guide models without changing the orbital equations
or the L1 ballistic solver. The following boundaries keep the fidelity layers
explicit.

## Guide-demand input

A future guide model should consume an immutable demand record containing only
quantities already produced by OR-1.1:

- node or route-leg identifier;
- geocentric entry and exit velocity vectors;
- required deflection angle and delta-v;
- rotor-element mass and passage frequency;
- allowed lateral acceleration abstraction;
- available guide length or requested guide-length solution;
- scenario and source manifest identifiers.

It must not reach into the ballistic solver or duplicate orbital equations.

## Magnet-model protocol

A magnet implementation can expose a protocol such as:

```python
class GuideModel(Protocol):
    fidelity_label: str
    def evaluate(self, demand: GuideDemand) -> GuideResult: ...
```

`GuideResult` may later carry field, gradient, current, geometry, loss, thermal,
and feasibility outputs. OR-1.1 intentionally defines none of those physical
relationships.

## Gravity and propagation protocol

If OR-2 introduces J2 or non-spherical Earth, add a propagation-model interface
that supplies acceleration and a fidelity label. Preserve the present spherical
two-body implementation as the L1 reference. New results must name their force
model and numerical tolerances in the manifest.

## Network and control protocol

The current static route maps active nodes to target nodes. A later controller
may consume node availability and emit a time-indexed route plan. It should
remain separate from:

- the arbitrary-stride ballistic primitive;
- steady rotor population scaling;
- guide-demand and magnet-response models.

This separation is necessary before modeling reroute transients, timing gaps,
element rephasing, sensor uncertainty, or actuator limits.

## Questions to resolve before implementation

1. Is guide acceleration prescribed, solved from a field model, or capped by
   both structural and electromagnetic constraints?
2. Are forces and power reported in the Earth-fixed guide frame, inertial
   frame, or both?
3. What finite guide envelope and node-clearance geometry constrains the L1
   trajectory?
4. Which higher-fidelity gravity model is the first accepted comparison case?
5. What transient routing policy and minimum separation apply after failures?
