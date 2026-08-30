"""Explicit, bounded parameter-sweep support with CSV and Parquet output."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import yaml

from orbital_ring.analysis import evaluate_scenario
from orbital_ring.config import ConfigurationError, Scenario, load_scenario
from orbital_ring.constants import MODEL_VERSION
from orbital_ring.manifest import discover_git_commit
from orbital_ring.units import parse_quantity


@dataclass(frozen=True)
class SweepConfig:
    sweep_id: str
    base_scenario: Path
    design: str
    active_dimensions: tuple[str, ...]
    dimensions: dict[str, tuple[Any, ...]]
    source_path: Path
    raw: dict[str, Any]


DIMENSION_SPECS: dict[str, tuple[str, str | None]] = {
    "ring.node_count": ("ring.node_count", None),
    "rotor.element_mass": ("rotor.element_mass_kg", "kg"),
    "rotor.geocentric_velocity": ("rotor.geocentric_velocity_m_s", "m/s"),
    "rotor.total_moving_mass": ("rotor.total_moving_mass_kg", "kg"),
    "ring.altitude": ("ring.altitude_m", "m"),
    "magnetic.max_lateral_acceleration": (
        "magnetic.max_lateral_acceleration_m_s2",
        "m/s^2",
    ),
    "safety.minimum_safe_altitude": ("safety.minimum_safe_altitude_m", "m"),
    "transfer.skip_nodes": ("transfer.skip_nodes", None),
}


def load_sweep_config(path: str | Path) -> SweepConfig:
    source = Path(path).resolve()
    try:
        raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"cannot load sweep configuration {source}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ConfigurationError("sweep root must be a mapping")
    required = ("sweep_id", "base_scenario", "design", "active_dimensions", "dimensions")
    missing = [key for key in required if key not in raw]
    if missing:
        raise ConfigurationError(f"missing sweep fields: {', '.join(missing)}")
    design = str(raw["design"]).lower()
    if design not in {"one_at_a_time", "cartesian"}:
        raise ConfigurationError("sweep design must be one_at_a_time or cartesian")
    active = raw["active_dimensions"]
    dimensions_raw = raw["dimensions"]
    if not isinstance(active, list) or not active:
        raise ConfigurationError("active_dimensions must be a non-empty list")
    if not isinstance(dimensions_raw, Mapping):
        raise ConfigurationError("dimensions must be a mapping")
    dimensions: dict[str, tuple[Any, ...]] = {}
    for name in active:
        if name not in DIMENSION_SPECS:
            raise ConfigurationError(f"unsupported active sweep dimension: {name}")
        if name not in dimensions_raw:
            raise ConfigurationError(f"active dimension {name} has no configured values")
        values = dimensions_raw[name]
        if not isinstance(values, list) or not values:
            raise ConfigurationError(f"dimension {name} must contain a non-empty list")
        dimensions[name] = tuple(values)
    base_path = (source.parent / str(raw["base_scenario"])).resolve()
    return SweepConfig(
        sweep_id=str(raw["sweep_id"]),
        base_scenario=base_path,
        design=design,
        active_dimensions=tuple(str(item) for item in active),
        dimensions=dimensions,
        source_path=source,
        raw=dict(raw),
    )


def _convert_dimension_value(dimension: str, value: Any) -> tuple[str, Any]:
    canonical_path, unit = DIMENSION_SPECS[dimension]
    if unit is None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigurationError(f"{dimension} values must be integers; got {value!r}")
        return canonical_path, value
    return canonical_path, parse_quantity(value, unit, f"dimensions.{dimension}")


def _override_design(config: SweepConfig) -> list[tuple[str, dict[str, Any]]]:
    converted = {
        dimension: tuple(_convert_dimension_value(dimension, value) for value in values)
        for dimension, values in config.dimensions.items()
    }
    if config.design == "one_at_a_time":
        designs: list[tuple[str, dict[str, Any]]] = [("baseline", {})]
        for dimension in config.active_dimensions:
            for index, (canonical_path, value) in enumerate(converted[dimension]):
                designs.append((f"{dimension}[{index}]", {canonical_path: value}))
        return designs

    # Cartesian expansion is intentionally isolated and must be authorized by
    # the CLI flag before this function is reached.
    designs = [("cartesian[0]", {})]
    for dimension in config.active_dimensions:
        expanded: list[tuple[str, dict[str, Any]]] = []
        for label, overrides in designs:
            for index, (canonical_path, value) in enumerate(converted[dimension]):
                updated = dict(overrides)
                updated[canonical_path] = value
                expanded.append((f"{label};{dimension}[{index}]", updated))
        designs = expanded
    return designs


def _flatten_result(label: str, scenario: Scenario, result) -> dict[str, Any]:
    ballistic = result.ballistic
    return {
        "design_point": label,
        "scenario_id": scenario.scenario_id,
        "configuration_hash": result.manifest.configuration_hash,
        "timestamp_utc": result.manifest.timestamp_utc,
        "git_commit": result.manifest.git_commit,
        "fidelity": result.manifest.fidelity,
        "warnings_json": json.dumps(result.manifest.warnings),
        "node_count": scenario.ring.node_count,
        "skip_nodes": scenario.transfer.skip_nodes,
        "altitude_m": scenario.ring.altitude_m,
        "rotor_velocity_m_s": scenario.rotor.geocentric_velocity_m_s,
        "total_rotor_mass_kg": scenario.rotor.total_moving_mass_kg,
        "element_mass_kg": scenario.rotor.element_mass_kg,
        "max_lateral_acceleration_m_s2": (
            scenario.magnetic.max_lateral_acceleration_m_s2
        ),
        "circular_velocity_m_s": result.closed_form.circular_velocity_m_s,
        "support_acceleration_m_s2": (
            result.closed_form.continuous_support_acceleration_m_s2
        ),
        "l0_total_guide_length_m": result.closed_form.total_guide_length_m,
        "l0_guide_length_per_node_m": result.closed_form.guide_length_per_node_m,
        "flight_time_s": None if ballistic is None else ballistic.flight_time_s,
        "minimum_ballistic_altitude_m": (
            None if ballistic is None else ballistic.minimum_altitude_m
        ),
        "active_deflection_angle_rad": (
            None if ballistic is None else ballistic.required_active_deflection_angle_rad
        ),
        "required_delta_v_m_s": (
            None if ballistic is None else ballistic.required_delta_v_m_s
        ),
        "intersects_earth": None if ballistic is None else ballistic.intersects_earth,
        "violates_minimum_safe_altitude": (
            None if ballistic is None else ballistic.violates_minimum_safe_altitude
        ),
        "number_of_elements": result.rotor_stream.number_of_elements,
        "passage_frequency_per_node_hz": (
            result.rotor_stream.element_passage_frequency_per_node_hz
        ),
        "kinetic_energy_per_element_j": (
            result.rotor_stream.kinetic_energy_per_element_j
        ),
        "average_node_reaction_force_n": (
            result.rotor_stream.average_node_reaction_force_mdot_n
        ),
    }


def run_sweep(
    config_path: str | Path,
    output_directory: str | Path,
    *,
    allow_cartesian: bool = False,
) -> pd.DataFrame:
    config = load_sweep_config(config_path)
    if config.design == "cartesian" and not allow_cartesian:
        raise ConfigurationError(
            "cartesian sweep refused; pass --allow-cartesian after reviewing its size"
        )
    base = load_scenario(config.base_scenario)
    designs = _override_design(config)
    rows: list[dict[str, Any]] = []
    complete_results: list[dict[str, Any]] = []
    for label, overrides in designs:
        scenario = base.with_overrides(overrides)
        result = evaluate_scenario(scenario)
        rows.append(_flatten_result(label, scenario, result))
        complete_results.append(result.to_dict())

    frame = pd.DataFrame(rows)
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output / "sweep_results.csv", index=False)
    frame.to_parquet(output / "sweep_results.parquet", index=False)
    (output / "sweep_results.json").write_text(
        json.dumps(complete_results, indent=2, allow_nan=False), encoding="utf-8"
    )
    canonical_sweep = json.dumps(config.raw, sort_keys=True, separators=(",", ":"))
    manifest = {
        "sweep_id": config.sweep_id,
        "sweep_configuration": config.raw,
        "sweep_configuration_hash": hashlib.sha256(
            canonical_sweep.encode("utf-8")
        ).hexdigest(),
        "base_scenario_inputs": base.canonical_inputs(),
        "model_version": MODEL_VERSION,
        "fidelity": base.model.fidelity,
        "git_commit": discover_git_commit(config.source_path),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "generated_design_points": len(frame),
        "warnings": ["L0 guide lengths are large-N scaling approximations."],
    }
    (output / "sweep_manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8"
    )
    return frame

