import math

import pytest

from orbital_ring.magnetic_field import MU_0_H_M
from orbital_ring.magnetic_rotors import (
    evaluate_permanent_magnet,
    evaluate_persistent_current_loop,
    evaluate_saturated_ferromagnet,
)
from orbital_ring.materials import load_material_registry


def test_source_registry_records_conditions():
    registry = load_material_registry()
    assert "vacoflux_50" in registry.identifiers
    for identifier in registry.identifiers:
        record = registry.get(identifier)
        assert record.source_url.startswith("https://")
        for prop in record.properties.values():
            assert prop.unit
            assert prop.temperature
            assert prop.field_condition
            assert prop.notes


def test_saturated_ferromagnet_and_permanent_moment_relationships():
    registry = load_material_registry()
    ferro = evaluate_saturated_ferromagnet(
        registry,
        material_identifier="vacoflux_50",
        element_mass_kg=0.05,
        magnetic_material_mass_fraction=0.8,
        utilization_factor=0.7,
        required_acceleration_m_s2=1000.0,
        available_gradient_t_m=100.0,
    )
    volume = 0.05 * 0.8 / registry.get("vacoflux_50").value("density_kg_m3")
    expected = 0.7 * 2.30 / MU_0_H_M * volume
    assert ferro.magnetic_moment_a_m2 == pytest.approx(expected)

    permanent = evaluate_permanent_magnet(
        registry,
        material_identifier="vacodym_902_tp",
        element_mass_kg=0.05,
        magnetic_material_mass_fraction=1.0,
        utilization_factor=0.85,
        required_acceleration_m_s2=1000.0,
        available_gradient_t_m=100.0,
    )
    assert permanent.magnetic_moment_a_m2 > 0.0
    assert permanent.demagnetizing_field_scale_t == pytest.approx(
        MU_0_H_M * 1_190_000.0
    )


def test_persistent_loop_moment_and_no_infield_extrapolation():
    registry = load_material_registry()
    self_field = evaluate_persistent_current_loop(
        registry,
        loop_mean_radius_m=0.02,
        turns=10,
        operating_current_a=80.0,
        support_mass_kg=0.05,
        operating_temperature_k=77.0,
        external_field_t=0.0,
        external_field_orientation="self-field",
        effective_conductor_radius_m=0.0005,
        required_acceleration_m_s2=1000.0,
        available_gradient_t_m=100.0,
    )
    assert self_field.magnetic_moment_a_m2 == pytest.approx(
        10.0 * 80.0 * math.pi * 0.02**2
    )
    assert self_field.current_source_condition_supported
    assert self_field.critical_current_margin_fraction == pytest.approx(
        (120.0 - 80.0) / 120.0
    )

    in_field = evaluate_persistent_current_loop(
        registry,
        loop_mean_radius_m=0.02,
        turns=10,
        operating_current_a=80.0,
        support_mass_kg=0.05,
        operating_temperature_k=77.0,
        external_field_t=1.0,
        external_field_orientation="perpendicular-to-tape",
        effective_conductor_radius_m=0.0005,
        required_acceleration_m_s2=1000.0,
        available_gradient_t_m=100.0,
    )
    assert not in_field.current_source_condition_supported
    assert in_field.critical_current_margin_fraction is None
