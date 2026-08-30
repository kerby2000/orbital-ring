from pathlib import Path

import pytest

from orbital_ring.config import load_scenario


@pytest.fixture(scope="session")
def reference_scenario():
    return load_scenario(Path(__file__).resolve().parents[1] / "scenarios" / "reference.yaml")
