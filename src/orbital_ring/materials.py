"""Traceable material and external benchmark registry access."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REPOSITORY_REGISTRY_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "materials" / "registry.json"
)
_PACKAGED_REGISTRY_PATH = (
    Path(__file__).resolve().parent / "data" / "materials" / "registry.json"
)
DEFAULT_REGISTRY_PATH = (
    _REPOSITORY_REGISTRY_PATH
    if _REPOSITORY_REGISTRY_PATH.exists()
    else _PACKAGED_REGISTRY_PATH
)


@dataclass(frozen=True)
class PropertyRecord:
    name: str
    value: float
    unit: str
    temperature: str
    field_condition: str
    notes: str


@dataclass(frozen=True)
class MaterialRecord:
    identifier: str
    category: str
    material: str
    grade: str
    source_organization: str
    source_title: str
    source_url: str
    publication_date: str | None
    accessed_date: str
    properties: dict[str, PropertyRecord]

    def value(self, name: str) -> float:
        try:
            return self.properties[name].value
        except KeyError as exc:
            raise KeyError(f"{self.identifier!r} has no property {name!r}") from exc


class MaterialRegistry:
    """Validated read-only view of the version-controlled JSON registry."""

    def __init__(self, records: dict[str, MaterialRecord], *, version: str) -> None:
        self._records = records
        self.version = version

    def get(self, identifier: str) -> MaterialRecord:
        try:
            return self._records[identifier]
        except KeyError as exc:
            raise KeyError(f"unknown material dataset {identifier!r}") from exc

    @property
    def identifiers(self) -> tuple[str, ...]:
        return tuple(sorted(self._records))


def _required(mapping: dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise ValueError(f"missing {context}.{key}")
    return mapping[key]


def load_material_registry(
    path: str | Path = DEFAULT_REGISTRY_PATH,
) -> MaterialRegistry:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    version = str(_required(raw, "registry_version", "registry"))
    accessed_date = str(_required(raw, "accessed_date", "registry"))
    datasets = _required(raw, "datasets", "registry")
    if not isinstance(datasets, dict) or not datasets:
        raise ValueError("registry.datasets must be a non-empty mapping")
    records: dict[str, MaterialRecord] = {}
    for identifier, dataset in datasets.items():
        if not isinstance(dataset, dict):
            raise TypeError(f"dataset {identifier!r} must be a mapping")
        source = _required(dataset, "source", identifier)
        properties_raw = _required(dataset, "properties", identifier)
        properties: dict[str, PropertyRecord] = {}
        for name, item in properties_raw.items():
            for field in ("value", "unit", "temperature", "field_condition", "notes"):
                _required(item, field, f"{identifier}.properties.{name}")
            properties[name] = PropertyRecord(
                name=name,
                value=float(item["value"]),
                unit=str(item["unit"]),
                temperature=str(item["temperature"]),
                field_condition=str(item["field_condition"]),
                notes=str(item["notes"]),
            )
        records[identifier] = MaterialRecord(
            identifier=identifier,
            category=str(_required(dataset, "category", identifier)),
            material=str(_required(dataset, "material", identifier)),
            grade=str(_required(dataset, "grade", identifier)),
            source_organization=str(
                _required(source, "organization", f"{identifier}.source")
            ),
            source_title=str(_required(source, "title", f"{identifier}.source")),
            source_url=str(_required(source, "url", f"{identifier}.source")),
            publication_date=(
                None
                if source.get("publication_date") is None
                else str(source["publication_date"])
            ),
            accessed_date=accessed_date,
            properties=properties,
        )
    return MaterialRegistry(records, version=version)
