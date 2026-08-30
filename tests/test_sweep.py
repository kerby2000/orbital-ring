import json
from pathlib import Path

import pandas as pd

from orbital_ring.sweep import run_sweep


def test_small_l0_sweep_writes_all_formats(tmp_path):
    scenario = tmp_path / "scenario.yaml"
    scenario.write_text(
        """scenario_id: sweep-test
earth:
  mean_radius: 6371 km
  gravitational_parameter: 3.986004418e14 m^3/s^2
  rotation_rate: 7.2921150e-5 rad/s
ring:
  altitude: 500 km
  node_count: 96
  plane: equatorial
  direction: prograde
rotor:
  geocentric_velocity: 12 km/s
  total_moving_mass: 1000 tonne
  element_mass: 50 g
magnetic:
  max_lateral_acceleration: 1000 g_0
safety:
  minimum_safe_altitude: 100 km
transfer:
  skip_nodes: 1
model:
  fidelity: L0
""",
        encoding="utf-8",
    )
    sweep = tmp_path / "sweep.yaml"
    sweep.write_text(
        """sweep_id: small-test
base_scenario: scenario.yaml
design: one_at_a_time
active_dimensions: [ring.node_count]
dimensions:
  ring.node_count: [48, 96]
""",
        encoding="utf-8",
    )
    output = tmp_path / "out"
    frame = run_sweep(sweep, output)
    assert len(frame) == 3  # explicit baseline plus two requested design points
    assert (output / "sweep_results.csv").exists()
    assert (output / "sweep_results.parquet").exists()
    assert (output / "sweep_results.json").exists()
    assert (output / "sweep_manifest.json").exists()
    assert len(pd.read_parquet(output / "sweep_results.parquet")) == 3
    manifest = json.loads((output / "sweep_manifest.json").read_text(encoding="utf-8"))
    assert manifest["generated_design_points"] == 3

