# Assumptions and exclusions

## Included assumptions

- Earth is a sphere with scenario-supplied mean radius, gravitational
  parameter, and constant rotation rate.
- The ring is equatorial and the stream is prograde.
- Nodes are fixed in the Earth-rotating frame and are point targets in L1.
- Rotor-element mass does not affect its ballistic path.
- A node changes velocity impulsively for ballistic trajectory reporting. The
  guide estimate maps that transition to constant normal acceleration and
  integrates relative speed in the Earth-fixed guide frame.
- Inertial velocity rotates at constant magnitude and angular rate through the
  ideal guide interaction.
- Guide inertial velocity is held constant during each short interaction;
  Earth rotation of the local frame and gravity during that finite interaction
  are omitted.
- The moving stream is uniformly phased. Population and passage-frequency
  values are means and can be fractional expected occupancies.
- The prescribed geocentric speed is the speed immediately after every node.
- Homogeneous-stride rotor scaling applies only when the entire regular stream
  actually uses that stride.
- A failed-node route maps each active node to the next active node. Its local
  bypass leg is not used to redefine the whole ring as stride 2 or 3.
- The static failure-route period is the sum of its modeled leg flight times;
  transient rerouting, rephasing, and control are omitted.
- OR-2 receives orbital/guide demand only through an immutable adapter built
  from accepted OR-1.1 results.
- Magnetic dipoles remain adiabatically aligned with the local field-gradient
  direction; orientation dynamics are not integrated.
- Ferromagnetic and permanent-magnet moment calculations include explicit
  material mass fraction and utilization/demagnetization factors.
- Quadrupole aperture field follows the ideal 2-D relationship `|B|=G r`.
- Aperture clearance, navigation floor, ripple amplitude/pitch, and stream
  separation are explicit study choices rather than hidden material facts.
- Neighbor coupling is a nearest-neighbor coaxial point-dipole worst case.

## Explicitly omitted physics

- Earth J2 and all higher gravity harmonics;
- oblate or otherwise non-spherical Earth geometry;
- Moon and Sun perturbations;
- atmosphere and aerodynamic drag;
- finite-length 3-D magnet topology, end fields, and FEM;
- coil/yoke winding layout, structural support, insulation, protection, and
  manufacturability;
- detailed REBCO in-field critical-current surfaces, AC loss, persistent
  joints, quench propagation, and cryogenic system design;
- hysteresis and anomalous loss outside source measurement domains;
- finite node or guide size and collision/clearance geometry;
- sensor, timing, navigation, and manufacturing uncertainty;
- active control and stability analysis;
- structural elasticity, vibration, and global ring flexibility;
- thermal models and radiative/conductive heat transfer;
- optimization, lifecycle, economics, and reliability;
- relativistic effects and collective rotor-element dynamics.

OR-2 includes a first-order nearest-neighbor magnetic check but omits coupled
chain dynamics, active dipole orientation, navigation control, thermal rise,
radiative rejection, fatigue, and rotor containment.

## Interpretation limits

L0 Earth-fixed physical guide lengths are large-node-count scaling estimates. Applying them to a
small number of nodes is useful only as a comparison scale. L1 provides a
ballistic point-intercept and node velocity discontinuity; it does not prove
that a finite guide can occupy that location without intersecting Earth or
other hardware. The allowed lateral acceleration is an input abstraction.
OR-2 can invert that abstraction or calculate it from an M1 dipole capability,
but no M0/M1 result is a production magnet design.

An Earth intersection flag does not stop mathematical propagation. Such a
result is infeasible under the model and must not be interpreted as a physical
trajectory.
