"""Machine-readable traceability manifest construction."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import Any, Iterable

from orbital_ring.config import Scenario
from orbital_ring.constants import MODEL_VERSION
from orbital_ring.results import Manifest


def discover_git_commit(start_path: str | Path | None = None) -> str | None:
    directory = Path(start_path or Path.cwd())
    if directory.is_file():
        directory = directory.parent
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=directory,
            check=True,
            capture_output=True,
            text=True,
            timeout=3.0,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = result.stdout.strip()
    return commit or None


def build_manifest(
    scenario: Scenario,
    *,
    derived_parameters: dict[str, Any],
    warnings: Iterable[str],
    fidelity: str,
) -> Manifest:
    return Manifest(
        scenario_id=scenario.scenario_id,
        input_parameters=scenario.canonical_inputs(),
        derived_parameters=derived_parameters,
        model_version=MODEL_VERSION,
        fidelity=fidelity,
        git_commit=discover_git_commit(scenario.source_path),
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        configuration_hash=scenario.configuration_hash,
        warnings=tuple(dict.fromkeys(warnings)),
    )

