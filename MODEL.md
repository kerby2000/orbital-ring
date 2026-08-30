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

In the many-node limit, the magnetic share of the full turning angle is

\[
\Theta_{mag}=2\pi\left(1-\frac{v_{orb}^2}{v^2}\right).
\]

Given allowed lateral magnetic acceleration \(a_{deflect}>0\), the associated
curvature radius and active guide-length scalings are

\[
\rho_{mag}=\frac{v^2}{a_{deflect}},
\]

\[
L_{mag,total}=\rho_{mag}\Theta_{mag}, \qquad
L_{mag,node}=\frac{L_{mag,total}}{N}.
\]

These guide lengths are **large-N L0 scaling approximations**, not a finite-node
magnet design. When \(v\leq v_{orb}\), the signed magnetic support/turning
interpretation changes; the code preserves the equation and emits a warning.

## L1: rotating-node numerical ballistic transfer

Between nodes, the rotor element obeys only the planar two-body equations:

\[
\dot{\mathbf r}=\mathbf v, \qquad
\dot{\mathbf v}=-\mu\frac{\mathbf r}{\lVert\mathbf r\rVert^3}.
\]

For node count \(N\) and skip parameter \(k\), where \(k=1\) targets the next
node and \(k=2\) bypasses one node, the Earth-fixed angular spacing is

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

## Rotor-stream scaling

For total moving mass \(M\), element mass \(m\), speed \(v\), numerical leg
time \(t_f\), and skip \(k\):

\[
n_e=\frac{M}{m}, \qquad
T_{circ}=t_f\frac{N}{k}.
\]

Assuming phases are uniformly populated, the mean passage frequency at every
node is

\[
f_{node}=\frac{n_e}{kT_{circ}}.
\]

The mean along-stream element spacing and per-element kinetic energy are

\[
d=\frac{vT_{circ}}{n_e}, \qquad
E_k=\frac12mv^2.
\]

For active turn angle \(\delta\) at constant allowed lateral acceleration
\(a_{deflect}\):

\[
L_{guide}=\frac{v^2\delta}{a_{deflect}}, \qquad
n_{guide}=f_{node}\frac{L_{guide}}{v}.
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

## Fidelity labels

- **L0**: closed-form spherical-Earth scaling.
- **L1**: numerical planar two-body propagation with rotating point targets.

No calculation in this repository claims higher fidelity.

