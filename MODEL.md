# Model definition

All calculations use SI internally. Configuration quantities are parsed with
Pint and dimensional YAML values must include units.

## Coordinate and sign conventions

The L1 frame is Earth-centred inertial and planar. At launch, the current node
is at

\[
\mathbf r_0 = [r, 0], \qquad r=R_E+h.
\]

Positive tangential velocity is prograde. The departure angle \(\gamma\) is
measured from local prograde tangent toward outward radial, so

\[
\mathbf v_0 = v[\sin\gamma,\cos\gamma].
\]

The supplied L1 implementation supports equatorial, prograde cases only.

## L0: closed-form scaling

For spherical two-body Earth gravity with gravitational parameter \(\mu\):

\[
g(r)=\frac{\mu}{r^2}.
\]

Circular and escape velocities are

\[
v_{orb}=\sqrt{\frac{\mu}{r}}, \qquad
v_{esc}=\sqrt{\frac{2\mu}{r}}.
\]

The continuous lateral magnetic support acceleration for a stream at
geocentric speed \(v\) is

\[
a_{mag}=\frac{v^2}{r}-g(r).
\]

The previously reported quantity

\[
\Theta_{mag,inertial-period}
=2\pi\left(1-\frac{v_{orb}^2}{v^2}\right)
\]

is the magnetic inertial velocity-direction change accumulated over the time
\(2\pi r/v\). It is retained under that explicit name; it is not the magnetic
turn accumulated during one circuit relative to Earth-fixed nodes.

For a prograde Earth-fixed ring, define relative tangential speed and circuit
period

\[
u=v-\omega_E r, \qquad
T_{rel}=\frac{2\pi r}{u}.
\]

The total inertial velocity-direction change supplied magnetically during that
Earth-relative circuit is

\[
\Theta_{mag,EF}
=\frac{a_{mag}}{v}T_{rel}
=\frac{2\pi r a_{mag}}{vu}.
\]

For allowed lateral acceleration \(a_{deflect}>0\), the fraction of the
Earth-fixed circumference that must be active is \(a_{mag}/a_{deflect}\).
Therefore the large-N physical guide length fixed to Earth is

\[
L_{guide,total,EF}
=2\pi r\frac{a_{mag}}{a_{deflect}}, \qquad
L_{guide,node,EF}=\frac{L_{guide,total,EF}}{N}.
\]

The inertial magnetic curvature radius \(v^2/a_{deflect}\) remains a useful
turning quantity, but multiplying it by \(\Theta_{mag,EF}\) would produce an
inertial path length rather than Earth-fixed guide length. The Earth-fixed
length above is a **large-N L0 kinematic scaling approximation**, not a finite
field or magnet design. When \(v\leq v_{orb}\), the signed support/turning
interpretation changes and the code emits a warning.

## L1: rotating-node numerical ballistic transfer

Between nodes, the rotor element obeys only the planar two-body equations:

\[
\dot{\mathbf r}=\mathbf v, \qquad
\dot{\mathbf v}=-\mu\frac{\mathbf r}{\lVert\mathbf r\rVert^3}.
\]

For node count \(N\) and **node stride** \(k\), where \(k=1\) targets the next
node, \(k=2\) bypasses one node, and \(k=3\) bypasses two nodes, the Earth-fixed
angular spacing is

\[
\Delta\lambda=\frac{2\pi k}{N}.
\]

The nominal surface/arc separation at ring radius is

\[
s=r\Delta\lambda.
\]

During the unknown flight time \(t_f\), the target rotates in inertial space to

\[
\mathbf r_{target}(t_f)=r
\begin{bmatrix}
\cos(\Delta\lambda+\omega_Et_f)\\
\sin(\Delta\lambda+\omega_Et_f)
\end{bmatrix}.
\]

The shooting variables are \(\gamma\) and \(t_f\). A DOP853 integration and
bounded nonlinear least-squares solve enforce
\(\mathbf r(t_f)=\mathbf r_{target}(t_f)\) while keeping the specified initial
geocentric speed fixed. The solver reports its terminal position error.

At arrival angle \(\phi=\Delta\lambda+\omega_Et_f\), the desired departure
velocity for the repeated next leg is the original departure velocity rotated
by \(\phi\):

\[
\mathbf v_{out,next}=\mathbf R(\phi)\mathbf v_0.
\]

The active deflection and node delta-v are

\[
\delta=\cos^{-1}\left(
\frac{\mathbf v_{in}\cdot\mathbf v_{out,next}}
{\lVert\mathbf v_{in}\rVert\lVert\mathbf v_{out,next}\rVert}
\right),
\]

\[
\Delta v=\lVert\mathbf v_{out,next}-\mathbf v_{in}\rVert.
\]

Minimum radius is found on the dense numerical solution over
\([0,t_f]\). The code flags \(r_{min}\leq R_E\) and a configurable
\(r_{min}<R_E+h_{safe}\).

### Earth-fixed guide kinematics

The guide interaction is separated into time, inertial path length, and
physical Earth-fixed length. Under ideal constant normal acceleration,

\[
t_{guide}=\frac{v\delta}{a_{deflect}}, \qquad
L_{turn,inertial}=v t_{guide}=\frac{v^2\delta}{a_{deflect}}.
\]

The second quantity is the rotor's inertial path through the turn and is not
the length of guide fixed to a node. At local radius \(r\), the guide inertial
velocity is

\[
\mathbf v_g=\boldsymbol\omega_E\times\mathbf r,
\qquad
\mathbf u(t)=\mathbf v(t)-\mathbf v_g.
\]

OR-1.1B rotates \(\mathbf v(t)\) at constant magnitude from the incoming to
outgoing local velocity at constant angular rate and evaluates

\[
L_{guide,EF}=\int_0^{t_{guide}}\lVert\mathbf u(t)\rVert\,dt
\]

with deterministic order-32 Gauss-Legendre quadrature. Earth rotation of the
local frame and gravity during the roughly 0.05--0.5 s interaction are omitted.
The result is an Earth-fixed kinematic physical-guide estimate, not a finite
field magnet simulation.

### Failure-route topology

Node stride describes one ballistic leg, not the complete network. A static
route maps every active node to the next active prograde node. With one failed
node, its upstream node has one local stride-two leg and all other active
upstream nodes retain stride-one legs. Two adjacent failures produce one local
stride-three leg. OR-1.1 reports bypass geometry separately from normal
direct-ring reference quantities.

The approximate static route period is the sum of the flight times of the
normal and bypass legs actually in the route. Active-node passage frequency is
\(n_e/T_{route}\), while failed-node frequency is zero. This is distinct from
the invalid interpretation of a homogeneous stride-two ring.

Route legs and active-node transitions are separate. At each active node, the
arrival velocity is taken from its incoming leg's ballistic primitive and the
departure velocity from its outgoing leg's primitive, both rotated into local
radial/tangential coordinates. A one-node failure therefore produces mixed
stride 1-to-2 and 2-to-1 transitions at the two bypass endpoints; it does not
apply the periodic stride-2-to-2 turn at either guide. Two adjacent failures
similarly produce mixed stride 1-to-3 and 3-to-1 transitions.

## Rotor-stream scaling

For total moving mass \(M\), element mass \(m\), speed \(v\), numerical leg
time \(t_f\), and a genuinely homogeneous stride \(k\):

\[
n_e=\frac{M}{m}, \qquad
T_{circ}=t_f\frac{N}{k}.
\]

Assuming phases are uniformly populated, the mean passage frequency at every
node is

\[
f_{node}=\frac{n_e}{kT_{circ}}.
\]

The mean inertial along-stream element spacing and per-element kinetic energy
are

\[
d_{inertial}=\frac{vT_{circ}}{n_e}, \qquad
E_k=\frac12mv^2.
\]

The representative guide-frame spacing at an active node is

\[
d_{guide}=\frac{\overline{\lVert\mathbf u\rVert}}{f_{node}}.
\]

Guide occupancy uses interaction time directly, rather than inferring it from
an inertial path mislabeled as physical length:

\[
n_{guide}=f_{node}t_{guide}.
\]

The momentum-flow reaction magnitude is

\[
F_{node}=\dot m\Delta v, \qquad \dot m=f_{node}m.
\]

For the independent simultaneous-element check, the lateral force direction
rotates through \(\delta\). Its vector-sum projection factor is
\(2\sin(\delta/2)/\delta\), giving

\[
F_{sum}=n_{guide}ma_{deflect}
\frac{2\sin(\delta/2)}{\delta}.
\]

Because \(\Delta v=2v\sin(\delta/2)\) for equal endpoint speeds,
\(F_{sum}=F_{node}\) algebraically. The code reports their numerical relative
error.

## Global force closure

For a regular direct-routing ring, the finite-node validation compares

\[
F_{L1,sum}(N)=N F_{node,L1}
\]

with the continuous-ring support force

\[
F_{continuous}=M\left(\frac{v^2}{r}-\frac{\mu}{r^2}\right).
\]

As \(N\) grows, the L1 ballistic deflection divided by leg time converges to
the continuous support acceleration. OR-1.1 reports the signed and absolute
relative finite-node error instead of treating L0 as exact at small \(N\).

## OR-2 guide-demand boundary

OR-2 magnetic models consume an immutable `GuideDemand` assembled from the
accepted OR-1.1 `SimulationResult`. It contains local endpoint velocities,
turn angle, delta-v, element mass, passage frequency, node force,
guide-frame speeds/spacing, and legacy guide kinematics. Magnetic modules do
not call the ballistic solver or reproduce orbital equations.

For a fixed accepted velocity turn, interaction time and physical Earth-fixed
guide length scale inversely with ideal constant normal acceleration:

\[
t(a)=t_{ref}\frac{a_{ref}}{a},\qquad
L(a)=L_{ref}\frac{a_{ref}}{a}.
\]

This supports length-driven inversion \(a=a_{ref}L_{ref}/L_{target}\) and
capability-driven guide length. Net vector impulse is \(m\Delta v\); the
integrated magnitude of the rotating lateral force is separately reported as
\(mv\delta\). Node-average closure uses \(f_{node}m\Delta v\).

## M0 magnetic bounds

For field magnitude \(B\), Maxwell pressure and vacuum field-energy density
are

\[
p_B=u_B=\frac{B^2}{2\mu_0}.
\]

The ideal area scale \(F/p_B\) is an absolute force-density sanity bound, not
a rotor force law or coil design.

## M1 quadrupole and aligned dipole

The ideal current-free 2-D normal quadrupole surrogate uses
\(\mathbf B=(Gx,-Gy)\), so \(|B|=Gr\). For aperture radius \(a\),

\[
B_{pt}=Ga,\qquad
U'_{aperture}=\int_A\frac{B^2}{2\mu_0}dA
=\frac{\pi G^2a^4}{4\mu_0}.
\]

Only aperture field energy is included. Coil/yoke/end fields and mechanical
support increase real stored energy. The external MQXF values (150-mm clear
aperture, 132.6 T/m nominal gradient, about 11.4 T peak conductor field) are a
scale comparison, not an orbital-guide mass claim.

For an adiabatically aligned point dipole,

\[
F\simeq\mu G,\qquad a\simeq\frac{\mu}{m}G,\qquad
G_{required}=\frac{a}{\mu/m}.
\]

Thus at fixed specific moment \(\mu/m\), reducing mass reduces moment and
force in proportion but does not reduce required gradient. High-field-seeking
dipoles are not guaranteed passive 3-D stability.

## M1 rotor concepts

For saturated soft material with source polarization \(J_s\), density
\(\rho\), magnetic mass fraction \(x\), and utilization \(\eta\):

\[
M_s=J_s/\mu_0,\quad V_m=xm/\rho,\quad \mu=\eta M_sV_m.
\]

The utilization factor makes demagnetization/geometry assumptions explicit;
saturation is never automatic. The permanent-magnet model uses the same
volume relationship with \(M\simeq B_r/\mu_0\), reports a \(\mu_0H_{cJ}\)
comparison scale, and preserves temperature warnings.

For a persistent-current loop,

\[
\mu=NIA,\qquad \ell_c=2\pi RN.
\]

The optional thin circular-loop inductance approximation is

\[
L\simeq\mu_0N^2R[\ln(8R/r_c)-2]
\]

and is accepted only for \(R/r_c\ge10\). Stored energy is \(LI^2/2\).
SuperPower's scalar 77-K self-field current range is used only at that exact
condition; in-field points are unsupported rather than extrapolated.

## Ripple, loss, aperture, packing, and coupling

Longitudinal segmentation ripple is distinct from the smooth transverse
gradient:

\[
B_{ripple}(s)=\Delta B\sin(2\pi s/\lambda),\qquad f=u_{guide}/\lambda.
\]

The LOSS-L1 thin-section comparison uses

\[
P_e/V=\frac{\pi^2B_p^2t^2f^2}{6\rho_e},\qquad
\delta_{skin}=\sqrt{\frac{2\rho_e}{2\pi f\mu_0\mu_r}}.
\]

It is flagged invalid for \(t/\delta_{skin}>0.3\). Manufacturer core loss is
not extrapolated. A separate conductive loop solves the sinusoidal steady
state of \(L\dot i+Ri=-\dot\Phi_{ext}\).

Spherical/cylindrical/loop envelopes feed the aperture rule

\[
a=max(c_r r_{rotor},a_{navigation}).
\]

Packing compares mean guide-frame center spacing with rotor envelope plus an
explicit surface-gap study margin. Worst-case coaxial neighbor coupling uses

\[
B_{nn}=\frac{\mu_0}{4\pi}\frac{2\mu}{s^3},\qquad
F_{nn}=\frac{3\mu_0\mu^2}{2\pi s^4}.
\]

The point-dipole result is considered reliable only above five rotor
diameters. Soft-ferromagnetic coupling is labeled as the guide-magnetized
worst case; free-flight moment may be much smaller.

## Fidelity labels

- **L0**: closed-form spherical-Earth scaling.
- **L1**: numerical planar two-body propagation with rotating point targets.
- **M0-PRESSURE**: Maxwell pressure/field-energy bound.
- **M1-GUIDE-KINEMATICS**: OR-1.1 demand length/capability inversion.
- **M1-QUADRUPOLE**: ideal circular-aperture gradient surrogate.
- **M1-DIPOLE**, **M1-FERRO**, **M1-PM**, **M1-SCLOOP**: analytic rotor force/moment models.
- **M1-INDUCTIVE**: simple sinusoidal conductive R-L loop benchmark.
- **LOSS-L1**: first-order ripple, skin-depth, and classical eddy comparison.

No calculation in this repository claims production magnet fidelity.
