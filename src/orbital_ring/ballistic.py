"""L1 numerical two-body shooting solver between rotating Earth-fixed nodes."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares, minimize_scalar

from orbital_ring.geometry import (
    node_angular_spacing,
    node_arc_separation,
    rotate_vector,
    target_node_position,
)
from orbital_ring.orbit import circular_orbital_velocity
from orbital_ring.results import BallisticResult


class BallisticConvergenceError(RuntimeError):
    """Raised when the shooting method cannot find an accurate interception."""


@dataclass(frozen=True)
class IntegratorSettings:
    """Named accuracy controls so numerical constants are explicit."""

    relative_tolerance: float = 2.0e-10
    absolute_tolerance: float = 1.0e-7
    maximum_step_fraction: float = 1.0 / 80.0
    target_position_tolerance_m: float = 0.25
    maximum_solver_evaluations: int = 120
    minimum_flight_time_s: float = 1.0e-3
    maximum_hyperbolic_time_factor: float = 12.0


DEFAULT_INTEGRATOR_SETTINGS = IntegratorSettings()


def two_body_derivative(_time_s: float, state: np.ndarray, mu_m3_s2: float) -> np.ndarray:
    position = state[:2]
    radius = float(np.linalg.norm(position))
    acceleration = -mu_m3_s2 * position / radius**3
    return np.array([state[2], state[3], acceleration[0], acceleration[1]])


def propagate_two_body(
    initial_position_m: np.ndarray,
    initial_velocity_m_s: np.ndarray,
    flight_time_s: float,
    mu_m3_s2: float,
    settings: IntegratorSettings = DEFAULT_INTEGRATOR_SETTINGS,
    *,
    dense_output: bool = False,
):
    """Numerically integrate the planar Newtonian two-body equations."""

    state0 = np.concatenate((initial_position_m, initial_velocity_m_s))
    solution = solve_ivp(
        two_body_derivative,
        (0.0, flight_time_s),
        state0,
        args=(mu_m3_s2,),
        method="DOP853",
        rtol=settings.relative_tolerance,
        atol=settings.absolute_tolerance,
        max_step=max(flight_time_s * settings.maximum_step_fraction, 1.0e-6),
        dense_output=dense_output,
    )
    if not solution.success:
        raise BallisticConvergenceError(f"two-body integration failed: {solution.message}")
    return solution


def _time_bounds(
    *,
    mu_m3_s2: float,
    radius_m: float,
    velocity_m_s: float,
    angular_spacing_rad: float,
    rotation_rate_rad_s: float,
    time_guess_s: float,
    settings: IntegratorSettings,
) -> tuple[float, float]:
    specific_energy = 0.5 * velocity_m_s**2 - mu_m3_s2 / radius_m
    if specific_energy < 0.0:
        semi_major_axis_m = -mu_m3_s2 / (2.0 * specific_energy)
        orbital_period_s = 2.0 * math.pi * math.sqrt(semi_major_axis_m**3 / mu_m3_s2)
        upper = min(0.98 * orbital_period_s, max(5.0 * time_guess_s, 300.0))
    else:
        upper = max(settings.maximum_hyperbolic_time_factor * time_guess_s, 300.0)

    # Ensure the rotating target does not advance more than one extra full turn;
    # this keeps the root on the requested first-transfer branch.
    if rotation_rate_rad_s > 0.0:
        one_extra_turn_s = (2.0 * math.pi + angular_spacing_rad) / rotation_rate_rad_s
        upper = min(upper, one_extra_turn_s)
    return settings.minimum_flight_time_s, upper


def _initial_guesses(
    *,
    mu_m3_s2: float,
    radius_m: float,
    velocity_m_s: float,
    angular_spacing_rad: float,
    rotation_rate_rad_s: float,
) -> tuple[float, list[tuple[float, float]]]:
    relative_tangential_speed = velocity_m_s - rotation_rate_rad_s * radius_m
    if relative_tangential_speed <= 0.0:
        raise BallisticConvergenceError(
            "rotor tangential speed must exceed the Earth-fixed node speed"
        )
    time_guess = radius_m * angular_spacing_rad / relative_tangential_speed
    circular = circular_orbital_velocity(mu_m3_s2, radius_m)
    missing_curvature_fraction = 1.0 - (circular / velocity_m_s) ** 2
    angle_guess = -0.5 * angular_spacing_rad * missing_curvature_fraction
    chord_time = (
        2.0 * radius_m * math.sin(angular_spacing_rad / 2.0) / relative_tangential_speed
    )
    guesses = [
        (angle_guess, time_guess),
        (0.5 * angle_guess, time_guess),
        (1.5 * angle_guess, time_guess),
        (-0.5 * angular_spacing_rad, chord_time),
        (0.0, time_guess),
        (angle_guess, 1.25 * time_guess),
    ]
    return time_guess, guesses


def _minimum_radius_on_solution(solution, flight_time_s: float) -> float:
    if solution.sol is None:
        raise BallisticConvergenceError("dense output is required for minimum-altitude search")

    def radius_at(time_s: float) -> float:
        return float(np.linalg.norm(solution.sol(time_s)[:2]))

    # The bounded minimizer handles non-symmetric paths caused by target rotation.
    minimum = minimize_scalar(
        radius_at,
        bounds=(0.0, flight_time_s),
        method="bounded",
        options={"xatol": max(1.0e-7 * flight_time_s, 1.0e-7)},
    )
    return min(radius_at(0.0), radius_at(flight_time_s), float(minimum.fun))


def solve_ballistic_intercept(
    *,
    earth_radius_m: float,
    altitude_m: float,
    node_count: int,
    rotor_velocity_m_s: float,
    mu_m3_s2: float,
    earth_rotation_rad_s: float,
    minimum_safe_altitude_m: float,
    skip_nodes: int = 1,
    settings: IntegratorSettings = DEFAULT_INTEGRATOR_SETTINGS,
) -> BallisticResult:
    """Shoot a fixed-speed rotor element to a rotating target node.

    The initial position is ``[r, 0]``. The unknowns are the radial departure
    angle relative to local prograde tangent and the flight time. The target
    advances by ``earth_rotation_rad_s * flight_time`` while the element is in
    free flight.
    """

    if node_count < 2:
        raise ValueError("node_count must be at least 2")
    if skip_nodes <= 0 or skip_nodes >= node_count:
        raise ValueError("skip_nodes must satisfy 1 <= skip_nodes < node_count")
    radius_m = earth_radius_m + altitude_m
    angular_spacing = node_angular_spacing(node_count, skip_nodes)
    initial_position = np.array([radius_m, 0.0], dtype=float)
    time_guess, guesses = _initial_guesses(
        mu_m3_s2=mu_m3_s2,
        radius_m=radius_m,
        velocity_m_s=rotor_velocity_m_s,
        angular_spacing_rad=angular_spacing,
        rotation_rate_rad_s=earth_rotation_rad_s,
    )
    min_time, max_time = _time_bounds(
        mu_m3_s2=mu_m3_s2,
        radius_m=radius_m,
        velocity_m_s=rotor_velocity_m_s,
        angular_spacing_rad=angular_spacing,
        rotation_rate_rad_s=earth_rotation_rad_s,
        time_guess_s=time_guess,
        settings=settings,
    )

    evaluation_count = 0

    def residual(parameters: np.ndarray) -> np.ndarray:
        nonlocal evaluation_count
        evaluation_count += 1
        departure_angle, log_time = parameters
        flight_time = math.exp(log_time)
        initial_velocity = rotor_velocity_m_s * np.array(
            [math.sin(departure_angle), math.cos(departure_angle)]
        )
        solution = propagate_two_body(
            initial_position,
            initial_velocity,
            flight_time,
            mu_m3_s2,
            settings,
        )
        final_position = solution.y[:2, -1]
        target_position = target_node_position(
            radius_m,
            node_count,
            skip_nodes,
            earth_rotation_rad_s,
            flight_time,
        )
        return (final_position - target_position) / radius_m

    candidates: list[tuple[float, np.ndarray]] = []
    bounds = (
        np.array([-0.5 * math.pi + 1.0e-5, math.log(min_time)]),
        np.array([0.5 * math.pi - 1.0e-5, math.log(max_time)]),
    )
    for angle_guess, candidate_time in guesses:
        clipped_time = min(max(candidate_time, min_time * 1.01), max_time * 0.99)
        fit = least_squares(
            residual,
            np.array([angle_guess, math.log(clipped_time)]),
            bounds=bounds,
            xtol=2.0e-12,
            ftol=2.0e-12,
            gtol=2.0e-12,
            max_nfev=settings.maximum_solver_evaluations,
            x_scale=np.array([max(abs(angle_guess), 0.03), 0.2]),
        )
        position_error_m = float(np.linalg.norm(fit.fun) * radius_m)
        candidates.append((position_error_m, fit.x))
        if position_error_m <= settings.target_position_tolerance_m:
            break

    position_error_m, parameters = min(candidates, key=lambda item: item[0])
    if position_error_m > settings.target_position_tolerance_m:
        raise BallisticConvergenceError(
            "intercept shooting did not converge: "
            f"best terminal error {position_error_m:.3f} m exceeds "
            f"{settings.target_position_tolerance_m:.3f} m"
        )

    departure_angle, log_time = parameters
    flight_time = math.exp(float(log_time))
    outgoing_velocity = rotor_velocity_m_s * np.array(
        [math.sin(departure_angle), math.cos(departure_angle)]
    )
    final_solution = propagate_two_body(
        initial_position,
        outgoing_velocity,
        flight_time,
        mu_m3_s2,
        settings,
        dense_output=True,
    )
    incoming_velocity = final_solution.y[2:, -1]
    target_angle = angular_spacing + earth_rotation_rad_s * flight_time
    next_outgoing_velocity = rotate_vector(outgoing_velocity, target_angle)
    dot = float(np.dot(incoming_velocity, next_outgoing_velocity))
    speed_product = float(np.linalg.norm(incoming_velocity) * np.linalg.norm(next_outgoing_velocity))
    cosine = max(-1.0, min(1.0, dot / speed_product))
    deflection_angle = math.acos(cosine)
    delta_v = float(np.linalg.norm(next_outgoing_velocity - incoming_velocity))
    minimum_radius = _minimum_radius_on_solution(final_solution, flight_time)
    minimum_altitude = minimum_radius - earth_radius_m

    return BallisticResult(
        node_angular_spacing_rad=angular_spacing,
        surface_arc_separation_m=node_arc_separation(radius_m, node_count, skip_nodes),
        flight_time_s=flight_time,
        outgoing_velocity_m_s=(float(outgoing_velocity[0]), float(outgoing_velocity[1])),
        incoming_velocity_m_s=(float(incoming_velocity[0]), float(incoming_velocity[1])),
        required_active_deflection_angle_rad=deflection_angle,
        required_delta_v_m_s=delta_v,
        minimum_altitude_m=minimum_altitude,
        intersects_earth=minimum_altitude <= 0.0,
        violates_minimum_safe_altitude=minimum_altitude < minimum_safe_altitude_m,
        skip_nodes=skip_nodes,
        terminal_position_error_m=position_error_m,
        solver_evaluations=evaluation_count,
    )

