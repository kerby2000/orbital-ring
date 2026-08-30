"""Static ring routing for direct operation and specified failed nodes.

This module deliberately separates a ballistic ``node_stride`` from topology.
A stride greater than one appears only on the local upstream bypass leg(s);
unaffected active nodes retain direct stride-one legs.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from orbital_ring.analysis import evaluate_scenario
from orbital_ring.ballistic import solve_ballistic_intercept
from orbital_ring.config import Scenario
from orbital_ring.geometry import rotate_vector
from orbital_ring.guide import evaluate_guide_kinematics
from orbital_ring.results import (
    BallisticResult,
    FailureBypassResult,
    FailureRouteResult,
    NodeTransitionResult,
    RouteLeg,
)


def build_ring_route(node_count: int, failed_nodes: Iterable[int] = ()) -> tuple[RouteLeg, ...]:
    """Route every active node to the next active prograde node."""

    if node_count < 2:
        raise ValueError("node_count must be at least 2")
    failed = frozenset(failed_nodes)
    if any(isinstance(node, bool) or not isinstance(node, int) for node in failed):
        raise ValueError("failed node indices must be integers")
    if any(node < 0 or node >= node_count for node in failed):
        raise ValueError("failed node indices must satisfy 0 <= node < node_count")
    if len(failed) >= node_count - 1:
        raise ValueError("a route requires at least two active nodes")

    legs: list[RouteLeg] = []
    for start_node in range(node_count):
        if start_node in failed:
            continue
        for stride in range(1, node_count):
            target_node = (start_node + stride) % node_count
            if target_node not in failed:
                bypassed = tuple(
                    (start_node + offset) % node_count for offset in range(1, stride)
                )
                legs.append(
                    RouteLeg(
                        start_node=start_node,
                        target_node=target_node,
                        node_stride=stride,
                        bypassed_nodes=bypassed,
                    )
                )
                break
    return tuple(legs)


def evaluate_failure_route(
    scenario: Scenario, failed_nodes: Iterable[int]
) -> FailureRouteResult:
    """Evaluate static routing around specified failures.

    Global reference quantities come from the normal stride-one ring. Only the
    exceptional local leg(s) receive bypass ballistic solves. No homogeneous
    stride-two rotor population is inferred.
    """

    if scenario.model.fidelity != "L1":
        raise ValueError("failure-route evaluation requires L1 fidelity")
    failed = tuple(sorted(set(failed_nodes)))
    route_legs = build_ring_route(scenario.ring.node_count, failed)
    normal_scenario = scenario.with_overrides({"transfer.node_stride": 1})
    normal_result = evaluate_scenario(normal_scenario)
    if normal_result.ballistic is None:
        raise AssertionError("L1 normal reference did not produce a ballistic result")

    ballistic_by_stride: dict[int, BallisticResult] = {
        1: normal_result.ballistic
    }

    def ballistic_for_stride(node_stride: int) -> BallisticResult:
        if node_stride not in ballistic_by_stride:
            ballistic_by_stride[node_stride] = solve_ballistic_intercept(
                earth_radius_m=scenario.earth.mean_radius_m,
                altitude_m=scenario.ring.altitude_m,
                node_count=scenario.ring.node_count,
                rotor_velocity_m_s=scenario.rotor.geocentric_velocity_m_s,
                mu_m3_s2=scenario.earth.gravitational_parameter_m3_s2,
                earth_rotation_rad_s=scenario.earth.rotation_rate_rad_s,
                minimum_safe_altitude_m=scenario.safety.minimum_safe_altitude_m,
                node_stride=node_stride,
            )
        return ballistic_by_stride[node_stride]

    bypass_results: list[FailureBypassResult] = []
    for leg in route_legs:
        if leg.node_stride == 1:
            continue
        ballistic = ballistic_for_stride(leg.node_stride)
        bypass_results.append(
            FailureBypassResult(
                start_node=leg.start_node,
                target_node=leg.target_node,
                bypassed_nodes=leg.bypassed_nodes,
                ballistic=ballistic,
            )
        )

    incoming_leg_by_node = {leg.target_node: leg for leg in route_legs}
    outgoing_leg_by_node = {leg.start_node: leg for leg in route_legs}
    transitions: list[NodeTransitionResult] = []
    guide_speed = scenario.earth.rotation_rate_rad_s * scenario.radius_m
    for node_index in sorted(outgoing_leg_by_node):
        incoming_leg = incoming_leg_by_node[node_index]
        outgoing_leg = outgoing_leg_by_node[node_index]
        incoming_ballistic = ballistic_for_stride(incoming_leg.node_stride)
        outgoing_ballistic = ballistic_for_stride(outgoing_leg.node_stride)
        incoming_target_angle = (
            incoming_ballistic.node_angular_spacing_rad
            + scenario.earth.rotation_rate_rad_s
            * incoming_ballistic.flight_time_s
        )
        incoming_local = rotate_vector(
            np.asarray(incoming_ballistic.incoming_velocity_m_s),
            -incoming_target_angle,
        )
        outgoing_local = np.asarray(outgoing_ballistic.outgoing_velocity_m_s)
        guide = evaluate_guide_kinematics(
            incoming_local_velocity_m_s=incoming_local,
            outgoing_local_velocity_m_s=outgoing_local,
            guide_tangential_speed_m_s=guide_speed,
            allowed_lateral_acceleration_m_s2=(
                scenario.magnetic.max_lateral_acceleration_m_s2
            ),
        )
        transitions.append(
            NodeTransitionResult(
                node_index=node_index,
                incoming_leg_stride=incoming_leg.node_stride,
                outgoing_leg_stride=outgoing_leg.node_stride,
                incoming_local_velocity_m_s=(
                    float(incoming_local[0]),
                    float(incoming_local[1]),
                ),
                outgoing_local_velocity_m_s=(
                    float(outgoing_local[0]),
                    float(outgoing_local[1]),
                ),
                actual_transition_angle_rad=guide.inertial_turn_angle_rad,
                actual_transition_delta_v_m_s=guide.required_delta_v_m_s,
                ideal_interaction_time_s=guide.ideal_interaction_time_s,
                guide_relative_entry_speed_m_s=(
                    guide.guide_relative_entry_speed_m_s
                ),
                guide_relative_exit_speed_m_s=(
                    guide.guide_relative_exit_speed_m_s
                ),
                physical_guide_length_estimate_m=(
                    guide.physical_guide_length_estimate_m
                ),
                inertial_turn_path_length_m=guide.inertial_turn_path_length_m,
                is_failure_related=(
                    incoming_leg.node_stride != 1
                    or outgoing_leg.node_stride != 1
                ),
            )
        )

    normal_leg_count = sum(leg.node_stride == 1 for leg in route_legs)
    route_period = sum(
        ballistic_for_stride(leg.node_stride).flight_time_s for leg in route_legs
    )
    number_of_elements = normal_result.rotor_stream.number_of_elements
    return FailureRouteResult(
        scenario_id=scenario.scenario_id,
        failed_nodes=failed,
        active_node_count=scenario.ring.node_count - len(failed),
        normal_leg_count=normal_leg_count,
        route_circulation_period_s=route_period,
        normal_reference_circulation_period_s=(
            normal_result.rotor_stream.circulation_period_s
        ),
        active_node_passage_frequency_hz=number_of_elements / route_period,
        normal_reference_passage_frequency_hz=(
            normal_result.rotor_stream.element_passage_frequency_per_node_hz
        ),
        route_legs=route_legs,
        bypass_legs=tuple(bypass_results),
        node_transitions=tuple(transitions),
        normal_global_reference=normal_result,
    )
