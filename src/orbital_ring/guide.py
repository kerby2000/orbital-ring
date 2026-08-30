"""OR-1.1 Earth-fixed guide-frame kinematic length estimates.

This is not a field or magnet model. It assumes the inertial velocity vector
rotates at constant magnitude and angular rate under ideal constant normal
acceleration while the local Earth-fixed guide velocity remains constant over
the short interaction.
"""

from __future__ import annotations

import math

import numpy as np

from orbital_ring.results import GuideKinematicsResult


GAUSS_LEGENDRE_ORDER = 32


def _signed_shortest_angle(incoming: np.ndarray, outgoing: np.ndarray) -> float:
    cross = float(incoming[0] * outgoing[1] - incoming[1] * outgoing[0])
    dot = float(np.dot(incoming, outgoing))
    return math.atan2(cross, dot)


def evaluate_guide_kinematics(
    *,
    incoming_local_velocity_m_s: tuple[float, float] | np.ndarray,
    outgoing_local_velocity_m_s: tuple[float, float] | np.ndarray,
    guide_tangential_speed_m_s: float,
    allowed_lateral_acceleration_m_s2: float,
) -> GuideKinematicsResult:
    """Integrate relative speed through an ideal constant-rate inertial turn.

    Local coordinates are outward radial then prograde tangential. Earth-frame
    rotation and gravity during the finite guide interaction are omitted at
    this fidelity; both endpoint inertial speeds must therefore agree.
    """

    incoming = np.asarray(incoming_local_velocity_m_s, dtype=float)
    outgoing = np.asarray(outgoing_local_velocity_m_s, dtype=float)
    if incoming.shape != (2,) or outgoing.shape != (2,):
        raise ValueError("incoming and outgoing velocities must be planar vectors")
    if allowed_lateral_acceleration_m_s2 <= 0.0:
        raise ValueError("allowed lateral acceleration must be positive")
    incoming_speed = float(np.linalg.norm(incoming))
    outgoing_speed = float(np.linalg.norm(outgoing))
    if not math.isclose(incoming_speed, outgoing_speed, rel_tol=1.0e-8, abs_tol=1.0e-6):
        raise ValueError("ideal guide kinematics requires equal endpoint inertial speeds")
    inertial_speed = 0.5 * (incoming_speed + outgoing_speed)
    signed_angle = _signed_shortest_angle(incoming, outgoing)
    turn_angle = abs(signed_angle)
    delta_v = float(np.linalg.norm(outgoing - incoming))
    interaction_time = inertial_speed * turn_angle / allowed_lateral_acceleration_m_s2
    inertial_path_length = inertial_speed * interaction_time
    guide_velocity = np.array([0.0, guide_tangential_speed_m_s])
    relative_entry = float(np.linalg.norm(incoming - guide_velocity))
    relative_exit = float(np.linalg.norm(outgoing - guide_velocity))

    if turn_angle == 0.0:
        physical_length = 0.0
        representative_relative_speed = relative_entry
    else:
        nodes, weights = np.polynomial.legendre.leggauss(GAUSS_LEGENDRE_ORDER)
        fractions = 0.5 * (nodes + 1.0)
        incoming_direction = math.atan2(incoming[1], incoming[0])
        directions = incoming_direction + signed_angle * fractions
        velocities = inertial_speed * np.column_stack(
            (np.cos(directions), np.sin(directions))
        )
        relative_speeds = np.linalg.norm(velocities - guide_velocity, axis=1)
        representative_relative_speed = float(0.5 * np.dot(weights, relative_speeds))
        physical_length = interaction_time * representative_relative_speed

    return GuideKinematicsResult(
        inertial_rotor_speed_m_s=inertial_speed,
        guide_tangential_speed_m_s=guide_tangential_speed_m_s,
        guide_relative_entry_speed_m_s=relative_entry,
        guide_relative_exit_speed_m_s=relative_exit,
        representative_guide_relative_speed_m_s=representative_relative_speed,
        ideal_interaction_time_s=interaction_time,
        inertial_turn_angle_rad=turn_angle,
        required_delta_v_m_s=delta_v,
        physical_guide_length_estimate_m=physical_length,
        inertial_turn_path_length_m=inertial_path_length,
        quadrature_method=f"Gauss-Legendre order {GAUSS_LEGENDRE_ORDER}",
    )
