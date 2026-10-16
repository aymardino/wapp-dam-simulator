"""Exports the demonstration day of the website (Reference 2024 scenario, 24 h) as JSON, for the video.

Same computation as GET /api/v1/demo (api/main.py): run from the repository root,
    python video/scripts/export_demo.py > video/assets/demo.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.clearing import run_clearing, PROF, LOAD_WA  # noqa: E402
from engine.scenarios import scenario_rows  # noqa: E402

sup, dem, ntc = scenario_rows('reference_2024')
res = run_clearing(None, None, horizon=24, reference_rows=(sup, dem), ntc_override=ntc)
s = res['summary']
out = {
    'scenario': 'reference_2024', 'hours': s['hours'], 'prices': res['prices'], 'flows': res['flows'],
    'ntc': s['rules']['ntc'], 'welfare': res['welfare'], 'volume': res['volume'], 'net_pos': s['net_pos'],
    'saturated_lines': sum(1 for line in s['lines'].values() if line['saturated_hours'] > 0),
    'solver': s['solver'],
    'supply': [{k: r[k] for k in ('zone', 'actor', 'segment', 'quantity', 'price', 'profile')} for r in sup],
    'demand': [{k: r[k] for k in ('zone', 'actor', 'segment', 'quantity', 'price')} for r in dem],
    'profiles': {k: list(v) for k, v in PROF.items()}, 'load': list(LOAD_WA),
    'lines': {k: {'saturated_hours': v['saturated_hours']} for k, v in s['lines'].items()},
}
json.dump(out, sys.stdout, ensure_ascii=False, separators=(',', ':'))
