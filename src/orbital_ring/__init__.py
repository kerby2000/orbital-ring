"""Traceable orbital-ring simulation kernel."""

from orbital_ring.analysis import evaluate_scenario
from orbital_ring.ballistic import solve_ballistic_intercept
from orbital_ring.config import Scenario, load_scenario
from orbital_ring.guide import evaluate_guide_kinematics
from orbital_ring.network import build_ring_route, evaluate_failure_route

__all__ = [
    "Scenario",
    "evaluate_scenario",
    "load_scenario",
    "solve_ballistic_intercept",
    "build_ring_route",
    "evaluate_failure_route",
    "evaluate_guide_kinematics",
]

__version__ = "0.3.0"
