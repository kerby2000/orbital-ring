"""Strict YAML scenario loading and canonical configuration hashing."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from orbital_ring.units import parse_quantity


class ConfigurationError(ValueError):
    """Raised when a scenario is incomplete or unsupported."""


@dataclass(frozen=True)
class EarthConfig:
    mean_radius_m: float
    gravitational_parameter_m3_s2: float
    rotation_rate_rad_s: float


@dataclass(frozen=True)
class RingConfig:
    altitude_m: float
    node_count: int
    plane: str
    direction: str


@dataclass(frozen=True)
class RotorConfig:
    geocentric_velocity_m_s: float
    total_moving_mass_kg: float
    element_mass_kg: float


@dataclass(frozen=True)
class MagneticConfig:
    max_lateral_acceleration_m_s2: float


@dataclass(frozen=True)
class SafetyConfig:
    minimum_safe_altitude_m: float


@dataclass(frozen=True)
class TransferConfig:
    skip_nodes: int


@dataclass(frozen=True)
class ModelConfig:
    fidelity: str


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    earth: EarthConfig
    ring: RingConfig
    rotor: RotorConfig
    magnetic: MagneticConfig
    safety: SafetyConfig
    transfer: TransferConfig
    model: ModelConfig
    source_path: str | None = None

    @property
    def radius_m(self) -> float:
        return self.earth.mean_radius_m + self.ring.altitude_m

    def canonical_inputs(self) -> dict[str, Any]:
        """Return all physical inputs in SI, excluding the non-physical path."""

        data = asdict(self)
        data.pop("source_path", None)
        return data

    @property
    def configuration_hash(self) -> str:
        encoded = json.dumps(
            self.canonical_inputs(), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def with_overrides(self, overrides: Mapping[str, Any]) -> "Scenario":
        """Create a validated scenario with canonical SI-field overrides.

        Sweep code uses this method after it has converted YAML quantities.
        Supported paths are intentionally explicit.
        """

        data = self.canonical_inputs()
        supported = {
            "ring.node_count",
            "ring.altitude_m",
            "rotor.geocentric_velocity_m_s",
            "rotor.element_mass_kg",
            "rotor.total_moving_mass_kg",
            "magnetic.max_lateral_acceleration_m_s2",
            "safety.minimum_safe_altitude_m",
            "transfer.skip_nodes",
        }
        for path, value in overrides.items():
            if path not in supported:
                raise ConfigurationError(f"unsupported sweep override: {path}")
            section, key = path.split(".", maxsplit=1)
            data[section][key] = value
        return scenario_from_canonical(data, source_path=self.source_path)


def _mapping(parent: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    if key not in parent:
        raise ConfigurationError(f"missing required section: {key}")
    value = parent[key]
    if not isinstance(value, Mapping):
        raise ConfigurationError(f"{key} must be a mapping")
    return value


def _required(parent: Mapping[str, Any], key: str, path: str) -> Any:
    if key not in parent:
        raise ConfigurationError(f"missing required parameter: {path}.{key}")
    return parent[key]


def _positive(value: float, field: str, allow_zero: bool = False) -> float:
    valid = value >= 0.0 if allow_zero else value > 0.0
    if not valid:
        qualifier = "non-negative" if allow_zero else "positive"
        raise ConfigurationError(f"{field} must be {qualifier}; got {value}")
    return value


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigurationError(f"{field} must be a positive integer; got {value!r}")
    return value


def load_scenario(path: str | Path) -> Scenario:
    source = Path(path).resolve()
    try:
        raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigurationError(f"cannot read scenario {source}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"invalid YAML in {source}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ConfigurationError("scenario root must be a mapping")
    return scenario_from_yaml(raw, source_path=str(source))


def scenario_from_yaml(raw: Mapping[str, Any], source_path: str | None = None) -> Scenario:
    scenario_id = _required(raw, "scenario_id", "root")
    if not isinstance(scenario_id, str) or not scenario_id.strip():
        raise ConfigurationError("scenario_id must be a non-empty string")

    earth = _mapping(raw, "earth")
    ring = _mapping(raw, "ring")
    rotor = _mapping(raw, "rotor")
    magnetic = _mapping(raw, "magnetic")
    safety = _mapping(raw, "safety")
    transfer = _mapping(raw, "transfer")
    model = _mapping(raw, "model")

    canonical = {
        "scenario_id": scenario_id.strip(),
        "earth": {
            "mean_radius_m": parse_quantity(
                _required(earth, "mean_radius", "earth"), "m", "earth.mean_radius"
            ),
            "gravitational_parameter_m3_s2": parse_quantity(
                _required(earth, "gravitational_parameter", "earth"),
                "m^3/s^2",
                "earth.gravitational_parameter",
            ),
            "rotation_rate_rad_s": parse_quantity(
                _required(earth, "rotation_rate", "earth"),
                "rad/s",
                "earth.rotation_rate",
            ),
        },
        "ring": {
            "altitude_m": parse_quantity(
                _required(ring, "altitude", "ring"), "m", "ring.altitude"
            ),
            "node_count": _required(ring, "node_count", "ring"),
            "plane": _required(ring, "plane", "ring"),
            "direction": _required(ring, "direction", "ring"),
        },
        "rotor": {
            "geocentric_velocity_m_s": parse_quantity(
                _required(rotor, "geocentric_velocity", "rotor"),
                "m/s",
                "rotor.geocentric_velocity",
            ),
            "total_moving_mass_kg": parse_quantity(
                _required(rotor, "total_moving_mass", "rotor"),
                "kg",
                "rotor.total_moving_mass",
            ),
            "element_mass_kg": parse_quantity(
                _required(rotor, "element_mass", "rotor"),
                "kg",
                "rotor.element_mass",
            ),
        },
        "magnetic": {
            "max_lateral_acceleration_m_s2": parse_quantity(
                _required(magnetic, "max_lateral_acceleration", "magnetic"),
                "m/s^2",
                "magnetic.max_lateral_acceleration",
            )
        },
        "safety": {
            "minimum_safe_altitude_m": parse_quantity(
                _required(safety, "minimum_safe_altitude", "safety"),
                "m",
                "safety.minimum_safe_altitude",
            )
        },
        "transfer": {
            "skip_nodes": _required(transfer, "skip_nodes", "transfer")
        },
        "model": {"fidelity": _required(model, "fidelity", "model")},
    }
    return scenario_from_canonical(canonical, source_path=source_path)


def scenario_from_canonical(
    data: Mapping[str, Any], source_path: str | None = None
) -> Scenario:
    try:
        earth_data = data["earth"]
        ring_data = data["ring"]
        rotor_data = data["rotor"]
        magnetic_data = data["magnetic"]
        safety_data = data["safety"]
        transfer_data = data["transfer"]
        model_data = data["model"]
        node_count = _positive_int(ring_data["node_count"], "ring.node_count")
        skip_nodes = _positive_int(transfer_data["skip_nodes"], "transfer.skip_nodes")
        if skip_nodes >= node_count:
            raise ConfigurationError("transfer.skip_nodes must be less than ring.node_count")
        plane = str(ring_data["plane"]).lower()
        direction = str(ring_data["direction"]).lower()
        fidelity = str(model_data["fidelity"]).upper()
        if plane != "equatorial":
            raise ConfigurationError("OR-1 currently supports only an equatorial ring")
        if direction != "prograde":
            raise ConfigurationError("OR-1 currently supports only a prograde stream")
        if fidelity not in {"L0", "L1"}:
            raise ConfigurationError("model.fidelity must be L0 or L1")
        return Scenario(
            scenario_id=str(data["scenario_id"]),
            earth=EarthConfig(
                mean_radius_m=_positive(float(earth_data["mean_radius_m"]), "earth.mean_radius"),
                gravitational_parameter_m3_s2=_positive(
                    float(earth_data["gravitational_parameter_m3_s2"]),
                    "earth.gravitational_parameter",
                ),
                rotation_rate_rad_s=_positive(
                    float(earth_data["rotation_rate_rad_s"]),
                    "earth.rotation_rate",
                    allow_zero=True,
                ),
            ),
            ring=RingConfig(
                altitude_m=_positive(
                    float(ring_data["altitude_m"]), "ring.altitude", allow_zero=True
                ),
                node_count=node_count,
                plane=plane,
                direction=direction,
            ),
            rotor=RotorConfig(
                geocentric_velocity_m_s=_positive(
                    float(rotor_data["geocentric_velocity_m_s"]),
                    "rotor.geocentric_velocity",
                ),
                total_moving_mass_kg=_positive(
                    float(rotor_data["total_moving_mass_kg"]),
                    "rotor.total_moving_mass",
                ),
                element_mass_kg=_positive(
                    float(rotor_data["element_mass_kg"]), "rotor.element_mass"
                ),
            ),
            magnetic=MagneticConfig(
                max_lateral_acceleration_m_s2=_positive(
                    float(magnetic_data["max_lateral_acceleration_m_s2"]),
                    "magnetic.max_lateral_acceleration",
                )
            ),
            safety=SafetyConfig(
                minimum_safe_altitude_m=_positive(
                    float(safety_data["minimum_safe_altitude_m"]),
                    "safety.minimum_safe_altitude",
                    allow_zero=True,
                )
            ),
            transfer=TransferConfig(skip_nodes=skip_nodes),
            model=ModelConfig(fidelity=fidelity),
            source_path=source_path,
        )
    except KeyError as exc:
        raise ConfigurationError(f"missing canonical configuration field: {exc}") from exc

