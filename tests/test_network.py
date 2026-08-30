import pytest

from orbital_ring.analysis import evaluate_scenario
from orbital_ring.config import load_scenario
from orbital_ring.network import build_ring_route, evaluate_failure_route


def test_normal_route_contains_only_direct_legs():
    route = build_ring_route(8)
    assert len(route) == 8
    assert all(leg.node_stride == 1 for leg in route)
    assert all(not leg.bypassed_nodes for leg in route)


def test_one_failed_node_creates_one_local_stride_two_leg():
    route = build_ring_route(8, [2])
    bypasses = [leg for leg in route if leg.node_stride > 1]
    assert len(route) == 7
    assert sum(leg.node_stride == 1 for leg in route) == 6
    assert len(bypasses) == 1
    assert bypasses[0].start_node == 1
    assert bypasses[0].target_node == 3
    assert bypasses[0].node_stride == 2
    assert bypasses[0].bypassed_nodes == (2,)


def test_two_adjacent_failures_create_one_local_stride_three_leg():
    route = build_ring_route(8, [2, 3])
    bypasses = [leg for leg in route if leg.node_stride > 1]
    assert len(route) == 6
    assert sum(leg.node_stride == 1 for leg in route) == 5
    assert len(bypasses) == 1
    assert bypasses[0].start_node == 1
    assert bypasses[0].target_node == 4
    assert bypasses[0].node_stride == 3
    assert bypasses[0].bypassed_nodes == (2, 3)


def test_failure_route_does_not_publish_homogeneous_stride_two_frequency(reference_scenario):
    route = evaluate_failure_route(reference_scenario, [1])
    direct = evaluate_scenario(
        reference_scenario.with_overrides({"transfer.node_stride": 1})
    )
    homogeneous_stride_two = evaluate_scenario(
        reference_scenario.with_overrides({"transfer.node_stride": 2})
    )
    assert route.normal_leg_count == 94
    assert len(route.bypass_legs) == 1
    assert route.bypass_legs[0].ballistic.node_stride == 2
    assert route.normal_reference_passage_frequency_hz == pytest.approx(
        direct.rotor_stream.element_passage_frequency_per_node_hz
    )
    assert route.active_node_passage_frequency_hz != pytest.approx(
        homogeneous_stride_two.rotor_stream.element_passage_frequency_per_node_hz,
        rel=0.1,
    )


def test_one_failure_uses_two_mixed_stride_node_transitions(reference_scenario):
    route = evaluate_failure_route(reference_scenario, [1])
    affected = [item for item in route.node_transitions if item.is_failure_related]
    assert len(affected) == 2
    assert {(item.incoming_leg_stride, item.outgoing_leg_stride) for item in affected} == {
        (1, 2),
        (2, 1),
    }
    for transition in affected:
        assert transition.actual_transition_angle_rad == pytest.approx(
            0.06117075, abs=2.0e-8
        )
        assert transition.physical_guide_length_estimate_m == pytest.approx(
            861.0, abs=2.0
        )
        assert transition.actual_transition_angle_rad != pytest.approx(
            route.bypass_legs[0].ballistic.required_active_deflection_angle_rad,
            abs=1.0e-4,
        )


def test_two_adjacent_failures_use_mixed_stride_three_transitions(reference_scenario):
    route = evaluate_failure_route(reference_scenario, [1, 2])
    affected = [item for item in route.node_transitions if item.is_failure_related]
    assert len(affected) == 2
    assert {(item.incoming_leg_stride, item.outgoing_leg_stride) for item in affected} == {
        (1, 3),
        (3, 1),
    }
    for transition in affected:
        assert transition.actual_transition_angle_rad == pytest.approx(
            0.08154744, abs=2.0e-8
        )
        assert transition.physical_guide_length_estimate_m == pytest.approx(
            1_147.0, abs=2.0
        )
