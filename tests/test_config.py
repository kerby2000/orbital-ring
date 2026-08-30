from copy import deepcopy
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

