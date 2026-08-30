import math

import pytest

from orbital_ring.magnetic_field import MU_0_H_M
from orbital_ring.magnetic_geometry import (
    cylinder_geometry,
    evaluate_aperture,
    evaluate_neighbor_coupling,
    evaluate_stream_packing,
    sphere_geometry,
)


def test_geometry_and_navigation_floor():
    sphere = sphere_geometry(mass_kg=0.05, density_kg_m3=8000.0)
    assert sphere.volume_m3 == pytest.approx(0.05 / 8000.0)
    cylinder = cylinder_geometry(
        mass_kg=0.05, density_kg_m3=8000.0, length_to_diameter_ratio=2.0
    )
    assert (
        math.pi * cylinder.radius_m** 2 * cylinder.longitudinal_envelope_m
        == pytest.approx(cylinder.volume_m3)
    )
    aperture = evaluate_aperture(
        rotor_radius_m=0.0005, clearance_factor=2.5, navigation_margin_m=0.005
    )
    assert aperture.aperture_radius_m == pytest.approx(0.005)
    assert aperture.navigation_floor_active


def test_packing_overlap_flag():
    feasible = evaluate_stream_packing(
        rotor_longitudinal_envelope_m=0.01,
        guide_frame_spacing_m=0.03,
        required_surface_gap_factor=1.0,
    )
    assert not feasible.infeasible_overlap
    blocked = evaluate_stream_packing(
        rotor_longitudinal_envelope_m=0.01,
        guide_frame_spacing_m=0.019,
        required_surface_gap_factor=1.0,
    )
    assert blocked.infeasible_overlap


def test_point_dipole_neighbor_formulas():
    moment = 2.0
    spacing = 0.5
    result = evaluate_neighbor_coupling(
        magnetic_moment_a_m2=moment,
        center_spacing_m=spacing,
        rotor_characteristic_radius_m=0.01,
        guide_force_n=100.0,
        guide_operating_field_t=2.0,
        magnetic_state="permanent",
    )
    expected_field = MU_0_H_M * 2.0 * moment / (4.0 * math.pi * spacing**3)
    expected_force = 3.0 * MU_0_H_M * moment**2 / (2.0 * math.pi * spacing**4)
    assert result.nearest_neighbor_field_t == pytest.approx(expected_field)
    assert result.nearest_neighbor_force_n == pytest.approx(expected_force)
    assert result.point_dipole_valid
