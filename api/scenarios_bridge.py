"""Pont vers les scénarios du moteur (évite un import circulaire dans service.py)."""
from engine.scenarios import scenario_rows, scenario_list, SCENARIOS  # noqa: F401
