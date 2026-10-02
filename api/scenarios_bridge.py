"""Bridge to the engine scenarios (avoids a circular import in service.py)."""
from engine.scenarios import scenario_rows, scenario_list, SCENARIOS  # noqa: F401
