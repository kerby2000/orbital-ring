import math

import pytest

from orbital_ring.magnetic_losses import (
    evaluate_conductive_loop,
    evaluate_ripple_loss,
    lamination_eddy_loss_density_w_m3,
    ripple_frequency_hz,
)
from orbital_ring.materials import load_material_registry


def test_ripple_frequency_and_eddy_scaling():
    assert ripple_frequency_hz(11500.0, 10.0) == pytest.approx(1150.0)
    base = lamination_eddy_loss_density_w_m3(
        ripple_flux_density_amplitude_t=0.01,
        section_thickness_m=0.0001,
        frequency_hz=1000.0,
        electrical_resistivity_ohm_m=4e-7,
    )
    assert lamination_eddy_loss_density_w_m3(
        ripple_flux_density_amplitude_t=0.02,
        section_thickness_m=0.0001,
        frequency_hz=1000.0,
        electrical_resistivity_ohm_m=4e-7,
    ) == pytest.approx(4.0 * base)
    assert lamination_eddy_loss_density_w_m3(
        ripple_flux_density_amplitude_t=0.01,
        section_thickness_m=0.0002,
        frequency_hz=1000.0,
        electrical_resistivity_ohm_m=4e-7,
    ) == pytest.approx(4.0 * base)


def test_skin_depth_validity_and_source_domain_flags():
    registry = load_material_registry()
    result = evaluate_ripple_loss(
        registry,
        material_identifier="tdk_n87",
        guide_relative_speed_m_s=11500.0,
        longitudinal_pitch_m=0.1,
        ripple_flux_density_amplitude_t=0.01,
        section_thickness_m=0.0005,
        relative_permeability=2200.0,
    )
    assert result.ripple_frequency_hz == pytest.approx(115000.0)
    assert result.source_frequency_domain_supported is True
    assert result.thin_section_valid is (result.thickness_to_skin_depth_ratio <= 0.3)


def test_conductive_loop_matches_sinusoidal_steady_state():
    registry = load_material_registry()
    result = evaluate_conductive_loop(
        registry,
        conductor_identifier="copper_c10810",
        loop_radius_m=0.01,
        conductor_radius_m=0.0005,
        guide_relative_speed_m_s=100.0,
        longitudinal_pitch_m=1.0,
        ripple_flux_density_amplitude_t=0.02,
    )
    omega = 2.0 * math.pi * result.ripple_frequency_hz
    expected = result.induced_emf_amplitude_v / math.hypot(
        result.resistance_ohm, omega * result.inductance_h
    )
    assert result.current_amplitude_a == pytest.approx(expected)
    assert result.average_joule_power_w == pytest.approx(
        0.5 * expected**2 * result.resistance_ohm
    )
