"""Static ring routing for direct operation and specified failed nodes.

This module deliberately separates a ballistic ``node_stride`` from topology.
A stride greater than one appears only on the local upstream bypass leg(s);
unaffected active nodes retain direct stride-one legs.
"""

from __future__ import annotations

from collections.abc import Iterable

from orbital_ring.analysis import evaluate_scenario
from orbital_ring.ballistic import solve_ballistic_intercept
from orbital_ring.config import Scenario
from orbital_ring.results import (
    FailureBypassResult,
    FailureRouteResult,
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

    bypass_results: list[FailureBypassResult] = []
    for leg in route_legs:
        if leg.node_stride == 1:
            continue
        ballistic = solve_ballistic_intercept(
            earth_radius_m=scenario.earth.mean_radius_m,
            altitude_m=scenario.ring.altitude_m,
            node_count=scenario.ring.node_count,
            rotor_velocity_m_s=scenario.rotor.geocentric_velocity_m_s,
            mu_m3_s2=scenario.earth.gravitational_parameter_m3_s2,
            earth_rotation_rad_s=scenario.earth.rotation_rate_rad_s,
            minimum_safe_altitude_m=scenario.safety.minimum_safe_altitude_m,
            node_stride=leg.node_stride,
        )
        bypass_results.append(
            FailureBypassResult(
                start_node=leg.start_node,
                target_node=leg.target_node,
                bypassed_nodes=leg.bypassed_nodes,
                ballistic=ballistic,
            )
        )

    normal_leg_count = sum(leg.node_stride == 1 for leg in route_legs)
    route_period = (
        normal_leg_count * normal_result.ballistic.flight_time_s
        + sum(item.ballistic.flight_time_s for item in bypass_results)
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
        normal_global_reference=normal_result,
    )
