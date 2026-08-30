import pandas as pd
import pytest

from orbital_ring.evidence import dataframe_to_markdown
from orbital_ring.materials import load_material_registry
from orbital_ring.or2_evidence import (
    aperture_field_energy_table,
    ripple_loss_table,
    small_element_limit_table,
    specific_moment_gradient_table,
)


def test_specific_moment_table_exposes_mass_independent_gradient():
    table = specific_moment_gradient_table()
    subset = table[
        (table["target_acceleration_g0"] == 1000.0)
        & (table["specific_magnetic_moment_a_m2_kg"] == 100.0)
    ]
    assert len(subset) == 3
    assert subset["required_gradient_t_m"].nunique() == 1
    assert subset["force_per_element_n"].nunique() == 3


def test_smaller_elements_reduce_aperture_until_floor_and_expose_limits(
    reference_scenario,
):
    registry = load_material_registry()
    aperture = aperture_field_energy_table(reference_scenario, registry)
    assert aperture.iloc[-1]["required_gradient_t_m"] == pytest.approx(
        aperture.iloc[0]["required_gradient_t_m"]
    )
    assert aperture.iloc[-1]["pole_tip_field_t"] < aperture.iloc[0]["pole_tip_field_t"]
    assert (
        aperture.iloc[-1]["aperture_field_energy_per_length_j_m"]
        < aperture.iloc[0]["aperture_field_energy_per_length_j_m"]
    )
    assert bool(aperture.iloc[-1]["navigation_floor_active"])

    small = small_element_limit_table(reference_scenario, registry)
    assert {0.5, 0.1}.issubset(set(small["element_mass_g"]))
    assert small.iloc[-1]["packing_ratio"] > small.iloc[0]["packing_ratio"]
    assert bool(small.iloc[-1]["infeasible_overlap"])
    assert (
        small.iloc[-1]["neighbor_force_fraction_of_guide"]
        > small.iloc[0]["neighbor_force_fraction_of_guide"]
    )


def test_rebco_ripple_is_reported_without_unsupported_loss(reference_scenario):
    table = ripple_loss_table(reference_scenario, load_material_registry())
    fe_co = table[table["material_identifier"] == "vacoflux_50"]
    assert fe_co["thin_section_valid"].tolist() == [True, False, False]
    rebco = table[table["material_identifier"] == "superpower_ap_4mm"]
    assert len(rebco) == 3
    assert rebco["classical_eddy_loss_density_w_m3"].isna().all()
    assert rebco["warnings"].str.contains("unresolved").all()


def test_markdown_marks_unmodeled_values_explicitly():
    rendered = dataframe_to_markdown(
        pd.DataFrame([{"loss_w": float("nan"), "assumption": "first | second"}])
    )
    assert "not-modeled" in rendered
    assert "nan" not in rendered.lower()
    assert "first \\| second" in rendered
