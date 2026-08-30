"""Machine-readable traceability manifest construction."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any, Iterable

import numpy
import pint
import scipy

from orbital_ring.ballistic import DEFAULT_INTEGRATOR_SETTINGS
from orbital_ring.config import Scenario
from orbital_ring.constants import MODEL_VERSION
from orbital_ring.results import Manifest


def discover_git_context(
    start_path: str | Path | None = None,
) -> tuple[str | None, bool | None]:
    requested = Path(start_path or Path.cwd())
    if requested.is_file():
        requested = requested.parent
    package_checkout = Path(__file__).resolve().parents[2]
    candidates = tuple(dict.fromkeys((requested, package_checkout, Path.cwd())))
    for directory in candidates:
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
            continue
        commit = result.stdout.strip()
        if not commit:
            continue
        try:
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
                timeout=3.0,
            )
            dirty = bool(status.stdout.strip())
        except (OSError, subprocess.SubprocessError):
            dirty = None
        return commit, dirty
    return None, None


def discover_git_commit(start_path: str | Path | None = None) -> str | None:
    """Backward-compatible convenience wrapper for the source commit."""

    return discover_git_context(start_path)[0]


def runtime_traceability() -> dict[str, str]:
    return {
        "python_version": platform.python_version(),
        "numpy_version": numpy.__version__,
        "scipy_version": scipy.__version__,
        "pint_version": pint.__version__,
        "platform_information": platform.platform(),
    }


def numerical_traceability() -> dict[str, Any]:
    settings = DEFAULT_INTEGRATOR_SETTINGS
    return {
        "numerical_integrator": "scipy.integrate.solve_ivp:DOP853",
        "integrator_rtol": settings.relative_tolerance,
        "integrator_atol": settings.absolute_tolerance,
        "integrator_max_step_policy": (
            "max(flight_time_s * "
            f"{settings.maximum_step_fraction:.17g}, 1e-6 s)"
        ),
        "terminal_position_tolerance_m": settings.target_position_tolerance_m,
        "solver_algorithm": "scipy.optimize.least_squares:trust-region-reflective",
        "maximum_solver_evaluations": settings.maximum_solver_evaluations,
    }


def build_manifest(
    scenario: Scenario,
    *,
    derived_parameters: dict[str, Any],
    warnings: Iterable[str],
    fidelity: str,
) -> Manifest:
    source_commit, source_dirty = discover_git_context(scenario.source_path)
    runtime = runtime_traceability()
    numerical = numerical_traceability()
    return Manifest(
        scenario_id=scenario.scenario_id,
        input_parameters=scenario.canonical_inputs(),
        derived_parameters=derived_parameters,
        model_version=MODEL_VERSION,
        fidelity=fidelity,
        source_commit=source_commit,
        source_worktree_dirty=source_dirty,
        # A file cannot contain the hash of the commit that contains that same
        # file: changing the embedded hash changes the commit. CI provenance
        # records the artifact-producing checkout as source_commit instead.
        artifact_commit=None,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        configuration_hash=scenario.configuration_hash,
        **runtime,
        **numerical,
        warnings=tuple(dict.fromkeys(warnings)),
    )
