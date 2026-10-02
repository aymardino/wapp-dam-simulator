"""
Ligne de commande du moteur de clearing : fichiers CSV en entrée, JSON (et CSV des prix) en sortie.

Exemples :
    python -m engine.cli --reference --out resultat.json
    python -m engine.cli --supply vente.csv --demand achat.csv --blocks blocs.csv --hours 19 --out resultat.json
Colonnes attendues (en-tête CSV) :
    vente  : zone, player, actor, segment, quantity, price, profile
    achat  : zone, player, actor, segment, quantity, price
    blocs  : zone, player, name, side, quantity, price, h_start, h_end, parent_name, excl_group
    mic    : zone, player, actor, fixed_term, variable_term
    ntc    : u, v, mw
"""
import argparse, csv, json, sys


def _read(path):
    if not path:
        return []
    with open(path, newline='', encoding='utf-8') as f:
        rows = []
        for r in csv.DictReader(f):
            rows.append({k: (v if v not in ('', None) else None) for k, v in r.items()})
        return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Clearing day-ahead WAPP (P1 → P1bis → P2)")
    ap.add_argument('--reference', action='store_true', help="utiliser les données de référence des 14 zones")
    ap.add_argument('--supply'); ap.add_argument('--demand'); ap.add_argument('--blocks'); ap.add_argument('--mic'); ap.add_argument('--ntc')
    ap.add_argument('--hours', type=int, nargs='*', help="heures simulées (défaut : 0..23)")
    ap.add_argument('--pricing', default='complete'); ap.add_argument('--pab', default='euphemia'); ap.add_argument('--tie', default='prorata')
    ap.add_argument('--fill-missing', action='store_true', help="compléter les zones sans soumission avec la référence")
    ap.add_argument('--out', help="fichier JSON de sortie (défaut : sortie standard)")
    ap.add_argument('--prices-csv', help="fichier CSV des prix zonaux")
    a = ap.parse_args(argv)

    from engine.clearing import run_clearing, ClearingError
    try:
        ntc = {(r['u'], r['v']): float(r['mw']) for r in _read(a.ntc)} or None
        if a.reference and not (a.supply or a.demand):
            res = run_clearing(None, None, hours=a.hours, ntc_override=ntc, block_rows=_read(a.blocks),
                               mic_rows=_read(a.mic), pricing=a.pricing, pab_rule=a.pab, tie_rule=a.tie)
        else:
            res = run_clearing(_read(a.supply), _read(a.demand), hours=a.hours, ntc_override=ntc,
                               block_rows=_read(a.blocks), mic_rows=_read(a.mic), fill_missing_zones=a.fill_missing,
                               pricing=a.pricing, pab_rule=a.pab, tie_rule=a.tie)
    except ClearingError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 2
    text = json.dumps(res, indent=2, default=float, ensure_ascii=False)
    if a.out:
        with open(a.out, 'w', encoding='utf-8') as f:
            f.write(text)
    else:
        print(text)
    if a.prices_csv:
        hours = res['summary']['hours']
        with open(a.prices_csv, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(['hour'] + list(res['prices'].keys()))
            for h in hours:
                w.writerow([h] + [res['prices'][z][str(h)] for z in res['prices']])
    s = res['summary']
    print(f"welfare={s['welfare']:,.0f} volume={s['volume']:,.0f} MWh elapsed={s['elapsed']}s solver={s['solver']}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
