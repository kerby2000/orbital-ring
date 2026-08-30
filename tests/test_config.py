from pathlib import Path

import pytest
import yaml

from orbital_ring.analysis import evaluate_scenario
from orbital_ring.config import ConfigurationError, load_scenario, scenario_from_yaml
from orbital_ring.units import UnitError


ROOT = Path(__file__).resolve().parents[1]


def reference_mapping():
    return yaml.safe_load((ROOT / "scenarios" / "reference.yaml").read_text(encoding="utf-8"))


def test_reference_scenario_has_traceability_fields():
    scenario = load_scenario(ROOT / "scenarios" / "reference.yaml")
    result = evaluate_scenario(scenario)
    manifest = result.manifest
    assert manifest.scenario_id == scenario.scenario_id
    assert manifest.configuration_hash == scenario.configuration_hash
    assert len(manifest.configuration_hash) == 64
    assert manifest.input_parameters["ring"]["altitude_m"] == 500_000.0
    assert manifest.derived_parameters["geocentric_radius_m"] == 6_871_000.0
    assert manifest.model_version
    assert manifest.timestamp_utc
    assert manifest.source_commit
    assert manifest.artifact_commit is None
    assert manifest.python_version
    assert manifest.numpy_version
    assert manifest.scipy_version
    assert manifest.pint_version
    assert manifest.platform_information
    assert manifest.numerical_integrator.endswith("DOP853")
    assert manifest.integrator_rtol == 2.0e-10
    assert manifest.integrator_atol == 1.0e-7
    assert manifest.terminal_position_tolerance_m == 0.25
    assert manifest.maximum_solver_evaluations == 120
    assert "Earth-fixed guide velocity" in manifest.guide_kinematics_model
    assert manifest.guide_quadrature_method == "Gauss-Legendre order 32"
    assert isinstance(manifest.warnings, tuple)


def test_missing_physical_parameter_is_rejected():
    raw = reference_mapping()
    del raw["rotor"]["element_mass"]
    with pytest.raises(ConfigurationError, match="rotor.element_mass"):
        scenario_from_yaml(raw)


def test_unitless_physical_parameter_is_rejected():
    raw = reference_mapping()
    raw["ring"]["altitude"] = 500_000
    with pytest.raises(UnitError, match="unit-bearing"):
        scenario_from_yaml(raw)


def test_unsupported_geometry_is_rejected():
    raw = reference_mapping()
    raw["ring"]["plane"] = "polar"
    with pytest.raises(ConfigurationError, match="equatorial"):
        scenario_from_yaml(raw)


def test_legacy_skip_nodes_migrates_with_warning():
    raw = reference_mapping()
    raw["transfer"]["skip_nodes"] = raw["transfer"].pop("node_stride")
    scenario = scenario_from_yaml(raw)
    assert scenario.transfer.node_stride == 1
    assert "Deprecated transfer.skip_nodes" in scenario.configuration_warnings[0]
    result = evaluate_scenario(scenario)
    assert any("Deprecated transfer.skip_nodes" in item for item in result.manifest.warnings)


def test_stride_and_legacy_name_cannot_both_be_defined():
    raw = reference_mapping()
    raw["transfer"]["skip_nodes"] = 1
    with pytest.raises(ConfigurationError, match="must not define both"):
        scenario_from_yaml(raw)
