# Assumptions and exclusions

## Included assumptions

- Earth is a sphere with scenario-supplied mean radius, gravitational
  parameter, and constant rotation rate.
- The ring is equatorial and the stream is prograde.
- Nodes are fixed in the Earth-rotating frame and are point targets in L1.
- Rotor-element mass does not affect its ballistic path.
- A node changes velocity impulsively for trajectory reporting; guide length
  then maps that turn to a constant allowed lateral-acceleration abstraction.
- The moving stream is uniformly phased. Population and passage-frequency
  values are means and can be fractional expected occupancies.
- The prescribed geocentric speed is the speed immediately after every node.
- Homogeneous-stride rotor scaling applies only when the entire regular stream
  actually uses that stride.
- A failed-node route maps each active node to the next active node. Its local
  bypass leg is not used to redefine the whole ring as stride 2 or 3.
- The static failure-route period is the sum of its modeled leg flight times;
  transient rerouting, rephasing, and control are omitted.

## Explicitly omitted physics

- Earth J2 and all higher gravity harmonics;
- oblate or otherwise non-spherical Earth geometry;
- Moon and Sun perturbations;
- atmosphere and aerodynamic drag;
- all electromagnetic interactions and magnet topology;
- magnetic fringe fields, saturation, losses, quench behaviour, and power;
- finite node or guide size and collision/clearance geometry;
- sensor, timing, navigation, and manufacturing uncertainty;
- active control and stability analysis;
- structural elasticity, vibration, and global ring flexibility;
- thermal models and radiative/conductive heat transfer;
- optimization, lifecycle, economics, and reliability;
- relativistic effects and rotor-element interactions.

## Interpretation limits

L0 guide lengths are large-node-count scaling estimates. Applying them to a
small number of nodes is useful only as a comparison scale. L1 provides a
ballistic point-intercept and node velocity discontinuity; it does not prove
that a finite guide can occupy that location without intersecting Earth or
other hardware. The allowed lateral acceleration is an input abstraction, not
a magnet-design result.

An Earth intersection flag does not stop mathematical propagation. Such a
result is infeasible under the model and must not be interpreted as a physical
trajectory.
