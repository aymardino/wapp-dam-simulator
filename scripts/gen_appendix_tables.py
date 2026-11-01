"""Génère les tableaux LaTeX de l'annexe (offre, demande, NTC du cas 2024) à partir de engine/scenarios.py.
À lancer depuis la racine du dépôt : python scripts/gen_appendix_tables.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from engine.scenarios import REFERENCE_2024, NTC_2024, actor_name_en

NAMES = {'NGA':'Nigeria','GHA':'Ghana','CIV':"Côte d'Ivoire",'SEN':'Senegal','BFA':'Burkina Faso','MLI':'Mali',
         'NER':'Niger','BEN':'Benin','TGO':'Togo','GIN':'Guinea','SLE':'Sierra Leone','LBR':'Liberia','GMB':'The Gambia','GNB':'Guinea-Bissau'}
# Technologie retenue, d'après les fourchettes de coûts de docs/REFERENCE_DATA.md ; † = combustible à confirmer
TECH = {
 'Hydro Kainji-Jebba-Shiroro-Zungeru':'Hydro', 'Egbin':'Gas (steam)', 'Azura-Edo CCGT':'Gas (CCGT)', 'Okpai CCGT':'Gas (CCGT)',
 'NIPP et autres centrales gaz':'Gas', 'Hydro Akosombo-Kpong-Bui':'Hydro', 'CCGT TICO-Cenpower-Amandi':'Gas (CCGT)',
 'Sunon Asogli':'Gas', 'AKSA et autres OCGT':'Gas (OCGT)$^\\dagger$', 'Karpowership Ghana':'Gas (power ship)$^\\dagger$',
 'Solaire Ghana':'Solar', 'Hydro CI-Energies (Soubré, Taabo, Kossou, Buyo)':'Hydro', 'Azito CCGT':'Gas (CCGT)',
 'CIPREL':'Gas', 'Atinkou CCGT':'Gas (CCGT)', 'Thermique HFO (Aggreko et autres)':'HFO', "Solaire Côte d'Ivoire":'Solar',
 'OMVS Manantali-Félou (part Sénégal)':'Hydro', 'Solaire Sénégal':'Solar', "Éolien Taïba N'Diaye":'Wind',
 'Charbon Sendou':'Coal', 'CCGT gaz (Cap des Biches, Malicounda)':'Gas (CCGT)$^\\dagger$', 'Thermique HFO (Kounoune, Tobène, Bel-Air)':'HFO',
 'Solaire Burkina (Zagtouli, Nagréongo, Kodeni, Zina)':'Solar', 'Hydro Bagré-Kompienga':'Hydro', 'SONABEL thermique HFO':'HFO',
 'OMVS-Sélingué hydro (part Mali)':'Hydro', 'Solaire Mali (Kita, Ségou, Sikasso, Sanankoroba)':'Solar',
 'EDM-SA thermique HFO/diesel':'HFO, diesel', 'Solaire Niger (Gorou Banda, Niamey, Agadez)':'Solar',
 'Charbon Anou Araren':'Coal', 'NIGELEC diesel/HFO (Gorou Banda, Niamey)':'Diesel, HFO', 'Solaire Bénin (Illoulofin)':'Solar',
 'CEB Nangbéto (part Bénin)':'Hydro', 'Maria-Gléta':'Thermal (gas or HFO)$^\\dagger$', 'Thermique de location':'Rental thermal',
 'Solaire Togo (Blitta, Dapaong)':'Solar', 'CEB Nangbéto (part Togo)':'Hydro', 'Kékéli CCGT':'Gas (CCGT)',
 'ContourGlobal Lomé':'HFO (multi-fuel)$^\\dagger$', 'Hydro Souapiti-Kaleta-Garafiri':'Hydro', 'EDG thermique HFO (Tombo, Kipé)':'HFO',
 'Hydro Bumbuna':'Hydro', 'Karpowership Sierra Leone':'HFO (power ship)', 'EDSA thermique':'HFO, diesel',
 'Hydro Mount Coffee':'Hydro', 'LEC thermique HFO (Bushrod)':'HFO', 'Solaire Jambur':'Solar',
 'NAWEC thermique HFO (Brikama, Kotu)':'HFO', 'Karpowership Guinée-Bissau':'HFO (power ship)',
}
PROF = {'hydro':'hydro','solar':'solar','baseload':'baseload','peaker':'peaker','flat':'constant'}
PEAK_EST = {'CIV','SEN','BFA','MLI','NER','BEN','TGO','GIN'}
NTC_INFO = {  # actif, niveau
 ('NGA','BEN'):('330 kV Ikeja--Sakété','sourced'), ('NGA','NER'):('132 kV Birnin Kebbi--Niamey','sourced'),
 ('BEN','TGO'):('CEB 161 kV, 330 kV Sakété--Lomé','estimated'), ('TGO','GHA'):('330 kV Volta--Lomé C, 161 kV','estimated'),
 ('GHA','CIV'):('225 kV Prestea--Riviera','estimated'), ('GHA','BFA'):('225 kV Bolgatanga--Ouagadougou','sourced'),
 ('CIV','BFA'):('225 kV Ferkessédougou--Bobo-Dioulasso','sourced'), ('CIV','MLI'):('225 kV Ferkessédougou--Sikasso--Ségou','estimated'),
 ('CIV','LBR'):('CLSG 225 kV','sourced'), ('LBR','SLE'):('CLSG 225 kV','sourced'), ('SLE','GIN'):('CLSG 225 kV','sourced'),
 ('GIN','GNB'):('OMVG 225 kV loop','estimated'), ('GNB','GMB'):('OMVG 225 kV loop','estimated'),
 ('GMB','SEN'):('OMVG 225 kV loop','estimated'), ('SEN','MLI'):('OMVS 225 kV network','estimated'),
}
def tex(s): return s.replace('&', '\\&').replace('%', '\\%')
def fmt(n): return f'{n:,}'.replace(',', '{,}')
def segs(L): return '; '.join(fmt(q) + '\\,@\\,' + str(p) for q, p in L)

out = []
# ── Tableau A1 : offre ──
out.append(r'''\begin{table*}[p]
\centering
\scriptsize
\caption{Reference case 2024: sell orders. Each seller offers up to four segments, written as power (MW) @ price (USD/MWh); the hourly availability profile scales the power offered at each hour. Technologies follow the cost ranges of the reference data; $\dagger$: fuel to be confirmed.}\label{tab:app-supply}
\begin{tabular}{@{}l>{\raggedright\arraybackslash}p{0.30\textwidth}llr@{}}
\toprule
Zone & Seller & Technology & Profile & Segments: MW @ USD/MWh \\
\midrule''')
for z, items in REFERENCE_2024.items():
    first = True
    for it in items:
        if it[0] != 'S': continue
        _, name, sg, prof = it
        out.append(f"{NAMES[z] if first else ''} & {tex(actor_name_en(name))} & {TECH[name]} & {PROF[prof]} & {segs(sg)} \\\\")
        first = False
    out.append(r'\addlinespace[2pt]')
out[-1] = r'\bottomrule'
out.append(r'''\end{tabular}
\end{table*}
''')
# ── Tableau A2 : demande et bilan par pays ──
out.append(r'''\begin{table*}[p]
\centering
\footnotesize
\caption{Reference case 2024: buy orders and country totals. The buy price of each tranche is assumed; the quantities are modulated by the common load profile. Available capacity and peak demand are those retained in the reference data; (est.): estimated.}\label{tab:app-demand}
\begin{tabular}{@{}llrrl@{}}
\toprule
Zone & Buyer & Available supply (MW) & Peak demand (MW) & Tranches: MW @ USD/MWh \\
\midrule''')
for z, items in REFERENCE_2024.items():
    sup = sum(q for x in items if x[0] == 'S' for q, _ in x[2])
    for it in items:
        if it[0] == 'D':
            pk = sum(q for q, _ in it[2])
            pks = f"{pk:,}".replace(',', '{,}') + (' (est.)' if z in PEAK_EST else '')
            out.append(f"{NAMES[z]} & {tex(it[1])} & {sup:,} & {pks} & {segs(it[2])} \\\\".replace(f'{sup:,}', f'{sup:,}'.replace(',', '{,}')))
tot_s = sum(q for it in REFERENCE_2024.values() for x in it if x[0]=='S' for q,_ in x[2])
tot_d = sum(q for it in REFERENCE_2024.values() for x in it if x[0]=='D' for q,_ in x[2])
out.append(r'\midrule')
out.append(f"Total & & {tot_s:,} & {tot_d:,} & \\\\".replace(',', '{,}'))
out.append(r'''\bottomrule
\end{tabular}
\end{table*}
''')
# ── Tableau A3 : NTC ──
out.append(r'''\begin{table*}[p]
\centering
\footnotesize
\caption{Reference case 2024: net transfer capacities, applied in both directions. Sourced: capacity published by the operator or a project document; estimated: no published exchange capacity, value retained from the asset description.}\label{tab:app-ntc}
\begin{tabular}{@{}llrl@{}}
\toprule
Line & Asset & NTC (MW) & Data level \\
\midrule''')
for (u, v), mw in NTC_2024.items():
    a, lvl = NTC_INFO[(u, v)]
    out.append(f"{NAMES[u]}--{NAMES[v]} & {a} & {mw} & {lvl} \\\\")
out.append(r'''\bottomrule
\end{tabular}
\end{table*}''')
open('appendix_data.tex', 'w', encoding='utf-8').write('\n'.join(out))
print(tot_s, tot_d)
