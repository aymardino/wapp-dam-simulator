"""
Page 1 — Soumission des Offres
Supporte : offres stepwise simples, block orders, offres liees/exclusives.
"""
import os, base64
import streamlit as st
import pandas as pd
from engine import get_session, save_supply_offers, save_demand_bids, get_zone_supply, get_zone_demand, ZONES, ZONE_COLORS, PROF

CSS_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
with open(CSS_PATH, encoding='utf-8') as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

LOGO_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'wapp_logo.png')
with open(LOGO_PATH, 'rb') as f:
    logo_b64 = base64.b64encode(f.read()).decode()

PROFILE_NAMES = ['baseload', 'hydro', 'solar', 'peaker', 'flat']

if 'my_zone' not in st.session_state:
    st.warning("Connectez-vous d'abord sur la page d'accueil.")
    st.stop()

my_zone   = st.session_state['my_zone']
my_player = st.session_state['my_player']
session   = get_session()
phase     = session.get('phase', 'submission')

color = ZONE_COLORS.get(my_zone, '#1a6b3a')
st.markdown(
    f'<div class="wapp-header">'
    f'<img src="data:image/png;base64,{logo_b64}" height="50"/>'
    f'<div><h1>Soumission des Offres</h1>'
    f'<div class="subtitle">'
    f'<span class="zone-pill" style="background:{color}22;border:1.5px solid {color};color:{color};">{my_zone}</span>'
    f'&nbsp;&nbsp;{my_player}</div></div></div>', unsafe_allow_html=True)

if phase == 'cleared':
    st.warning("Le marche est **cloture**. Les soumissions ne sont plus acceptees. Consultez les resultats ou demandez a l'Admin de reuvrir le marche.")
    st.stop()

# ── Choix du type d'offre ─────────────────────────────────────────
st.markdown("## Type d'offres")
order_type = st.radio(
    "Quel type d'ordre voulez-vous soumettre ?",
    options=["Stepwise (escalier simple)", "Block Orders (tout-ou-rien)", "Linked / Exclusifs"],
    horizontal=True,
    key="order_type_radio"
)

st.markdown("---")

# ════════════════════════════════════════════════════════
# TYPE 1 : STEPWISE
# ════════════════════════════════════════════════════════
if order_type == "Stepwise (escalier simple)":
    st.markdown(f'<span class="order-type-badge ot-stepwise">Stepwise LP</span> Offres par segments prix/quantite — acceptation partielle possible', unsafe_allow_html=True)
    st.markdown("")

    tab_supply, tab_demand, tab_preview = st.tabs(["Offres de Vente (Production)", "Offres d'Achat (Demande)", "Recapitulatif"])

    # ── Vente ──
    with tab_supply:
        st.markdown(f"### Production — Zone **{my_zone}**")
        st.caption("Max 4 segments par acteur. Prix croissants = merit order.")

        existing_supply = get_zone_supply(my_zone)
        if existing_supply:
            st.success(f"{len(existing_supply)} segment(s) deja soumis.")

        if 'supply_rows' not in st.session_state:
            st.session_state.supply_rows = [
                {'actor': r['actor'], 'segment': r['segment'], 'quantity': r['quantity'], 'price': r['price'], 'profile': r.get('profile','baseload')}
                for r in existing_supply
            ] if existing_supply else [{'actor': '', 'segment': 0, 'quantity': 100.0, 'price': 50.0, 'profile': 'baseload'}]

        rows = st.session_state.supply_rows
        hcol = st.columns([3, 1, 2, 2, 2, 1])
        for col, lbl in zip(hcol, ["Acteur", "Seg.", "MW", "EUR/MWh", "Profil", ""]):
            col.markdown(f"<small style='color:#1a6b3a;font-weight:700;text-transform:uppercase;font-size:0.7rem;'>{lbl}</small>", unsafe_allow_html=True)

        to_del = []
        for i, row in enumerate(rows):
            c1,c2,c3,c4,c5,c6 = st.columns([3,1,2,2,2,1])
            rows[i]['actor']    = c1.text_input("a", value=row['actor'], key=f"sa_{i}", label_visibility="collapsed", placeholder="Nom centrale / acteur")
            rows[i]['segment']  = c2.number_input("s", value=int(row['segment']), min_value=0, max_value=3, key=f"ss_{i}", label_visibility="collapsed")
            rows[i]['quantity'] = c3.number_input("q", value=float(row['quantity']), min_value=0.0, step=10.0, key=f"sq_{i}", label_visibility="collapsed")
            rows[i]['price']    = c4.number_input("p", value=float(row['price']), min_value=0.0, max_value=500.0, step=1.0, key=f"sp_{i}", label_visibility="collapsed")
            rows[i]['profile']  = c5.selectbox("pr", PROFILE_NAMES, index=PROFILE_NAMES.index(row.get('profile','baseload')) if row.get('profile','baseload') in PROFILE_NAMES else 0, key=f"spr_{i}", label_visibility="collapsed")
            if c6.button("X", key=f"sdel_{i}"):
                to_del.append(i)
        for idx in reversed(to_del): rows.pop(idx)

        ca, cb = st.columns([1,2])
        if ca.button("+ Segment", use_container_width=True, key="sadd"):
            rows.append({'actor': '', 'segment': len(rows), 'quantity': 100.0, 'price': 80.0, 'profile': 'baseload'})
            st.rerun()
        if cb.button("Enregistrer offres de VENTE", type="primary", use_container_width=True, key="ssave"):
            valid = [r for r in rows if r['actor'].strip() and r['quantity'] > 0]
            if not valid: st.error("Aucun segment valide.")
            else:
                save_supply_offers(my_zone, my_player, valid)
                st.success(f"{len(valid)} segment(s) de vente enregistre(s).")
                st.rerun()

        with st.expander("Profils horaires"):
            st.markdown("| Profil | Description |\n|---|---|\n| **baseload** | Thermique stable 95%/24h |\n| **hydro** | Hydraulique flexible (60-100%) |\n| **solar** | Solaire PV (0% nuit, 100% midi) |\n| **peaker** | Turbine gaz / diesel 100%/24h |\n| **flat** | Disponibilite totale constante |")

    # ── Achat ──
    with tab_demand:
        st.markdown(f"### Demande — Zone **{my_zone}**")
        st.caption("La demande est modulee par le profil de charge ouest-africain (creux nuit, pic matin/soir).")

        existing_demand = get_zone_demand(my_zone)
        if 'demand_rows' not in st.session_state:
            st.session_state.demand_rows = [
                {'actor': r['actor'], 'segment': r['segment'], 'quantity': r['quantity'], 'price': r['price']}
                for r in existing_demand
            ] if existing_demand else [{'actor': '', 'segment': 0, 'quantity': 500.0, 'price': 180.0}]

        drows = st.session_state.demand_rows
        hdcol = st.columns([3,1,2,2,1])
        for col, lbl in zip(hdcol, ["Acheteur", "Seg.", "MW", "Prix Max (EUR/MWh)", ""]):
            col.markdown(f"<small style='color:#1a6b3a;font-weight:700;text-transform:uppercase;font-size:0.7rem;'>{lbl}</small>", unsafe_allow_html=True)

        to_del_d = []
        for i, row in enumerate(drows):
            c1,c2,c3,c4,c5 = st.columns([3,1,2,2,1])
            drows[i]['actor']    = c1.text_input("a", value=row['actor'], key=f"da_{i}", label_visibility="collapsed", placeholder="Nom acheteur / reseau")
            drows[i]['segment']  = c2.number_input("s", value=int(row['segment']), min_value=0, max_value=3, key=f"ds_{i}", label_visibility="collapsed")
            drows[i]['quantity'] = c3.number_input("q", value=float(row['quantity']), min_value=0.0, step=10.0, key=f"dq_{i}", label_visibility="collapsed")
            drows[i]['price']    = c4.number_input("p", value=float(row['price']), min_value=0.0, max_value=500.0, step=1.0, key=f"dp_{i}", label_visibility="collapsed")
            if c5.button("X", key=f"ddel_{i}"):
                to_del_d.append(i)
        for idx in reversed(to_del_d): drows.pop(idx)

        da, db = st.columns([1,2])
        if da.button("+ Segment", use_container_width=True, key="dadd"):
            drows.append({'actor': '', 'segment': len(drows), 'quantity': 200.0, 'price': 150.0})
            st.rerun()
        if db.button("Enregistrer offres d'ACHAT", type="primary", use_container_width=True, key="dsave"):
            valid_d = [r for r in drows if r['actor'].strip() and r['quantity'] > 0]
            if not valid_d: st.error("Aucun segment valide.")
            else:
                save_demand_bids(my_zone, my_player, valid_d)
                st.success(f"{len(valid_d)} segment(s) d'achat enregistre(s).")
                st.rerun()

    # ── Preview ──
    with tab_preview:
        supply_data = get_zone_supply(my_zone)
        demand_data = get_zone_demand(my_zone)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Offres de Vente")
            if supply_data:
                df_s = pd.DataFrame(supply_data)[['actor','segment','quantity','price','profile']]
                df_s.columns = ['Acteur','Seg.','MW','EUR/MWh','Profil']
                st.dataframe(df_s, use_container_width=True, hide_index=True)
                st.metric("Capacite totale", f"{int(df_s['MW'].sum()):,} MW")
            else: st.info("Aucune offre de vente.")
        with c2:
            st.markdown("#### Offres d'Achat")
            if demand_data:
                df_d = pd.DataFrame(demand_data)[['actor','segment','quantity','price']]
                df_d.columns = ['Acheteur','Seg.','MW','Prix Max']
                st.dataframe(df_d, use_container_width=True, hide_index=True)
                st.metric("Demande totale", f"{int(df_d['MW'].sum()):,} MW")
            else: st.info("Aucune offre d'achat.")

# ════════════════════════════════════════════════════════
# TYPE 2 : BLOCK ORDERS
# ════════════════════════════════════════════════════════
elif order_type == "Block Orders (tout-ou-rien)":
    st.markdown(f'<span class="order-type-badge ot-block">Block Orders</span> Acceptation totale ou rejet — util pour centrales avec cout fixe important', unsafe_allow_html=True)
    st.info("**Block order** : l'offre est acceptee entierement sur toutes les heures specifiees, ou rejetee. Pas d'acceptation partielle (fill-or-kill). Le solveur passe en MILP.")
    st.markdown("")

    # Block supply
    st.markdown("### Blocs de Vente")
    if 'block_supply' not in st.session_state:
        st.session_state.block_supply = [{'name': '', 'qty': 100.0, 'price': 50.0, 'h_start': 0, 'h_end': 23}]

    bsrows = st.session_state.block_supply
    bcols = st.columns([3,2,2,1,1,1])
    for col, lbl in zip(bcols, ["Nom du bloc", "MW", "EUR/MWh", "H debut", "H fin", ""]):
        col.markdown(f"<small style='color:#1a6b3a;font-weight:700;text-transform:uppercase;font-size:0.7rem;'>{lbl}</small>", unsafe_allow_html=True)
    to_del_bs = []
    for i, r in enumerate(bsrows):
        c1,c2,c3,c4,c5,c6 = st.columns([3,2,2,1,1,1])
        bsrows[i]['name']    = c1.text_input("n", value=r['name'], key=f"bsn_{i}", label_visibility="collapsed", placeholder="ex: NGA Baseload Nuit")
        bsrows[i]['qty']     = c2.number_input("q", value=float(r['qty']), min_value=0.0, step=10.0, key=f"bsq_{i}", label_visibility="collapsed")
        bsrows[i]['price']   = c3.number_input("p", value=float(r['price']), min_value=0.0, max_value=500.0, step=1.0, key=f"bsp_{i}", label_visibility="collapsed")
        bsrows[i]['h_start'] = c4.number_input("hs", value=int(r['h_start']), min_value=0, max_value=23, key=f"bshs_{i}", label_visibility="collapsed")
        bsrows[i]['h_end']   = c5.number_input("he", value=int(r['h_end']),   min_value=0, max_value=23, key=f"bshe_{i}", label_visibility="collapsed")
        if c6.button("X", key=f"bsdel_{i}"): to_del_bs.append(i)
    for idx in reversed(to_del_bs): bsrows.pop(idx)
    if st.button("+ Bloc de vente", key="bsadd"):
        bsrows.append({'name': '', 'qty': 200.0, 'price': 40.0, 'h_start': 0, 'h_end': 23})
        st.rerun()

    st.markdown("### Blocs d'Achat")
    if 'block_demand' not in st.session_state:
        st.session_state.block_demand = [{'name': '', 'qty': 100.0, 'price': 150.0, 'h_start': 8, 'h_end': 20}]

    bdrows = st.session_state.block_demand
    bcols2 = st.columns([3,2,2,1,1,1])
    for col, lbl in zip(bcols2, ["Nom du bloc", "MW", "Prix Max (EUR/MWh)", "H debut", "H fin", ""]):
        col.markdown(f"<small style='color:#e86c1a;font-weight:700;text-transform:uppercase;font-size:0.7rem;'>{lbl}</small>", unsafe_allow_html=True)
    to_del_bd = []
    for i, r in enumerate(bdrows):
        c1,c2,c3,c4,c5,c6 = st.columns([3,2,2,1,1,1])
        bdrows[i]['name']    = c1.text_input("n", value=r['name'], key=f"bdn_{i}", label_visibility="collapsed", placeholder="ex: Industrie Pointe")
        bdrows[i]['qty']     = c2.number_input("q", value=float(r['qty']), min_value=0.0, step=10.0, key=f"bdq_{i}", label_visibility="collapsed")
        bdrows[i]['price']   = c3.number_input("p", value=float(r['price']), min_value=0.0, max_value=500.0, step=1.0, key=f"bdp_{i}", label_visibility="collapsed")
        bdrows[i]['h_start'] = c4.number_input("hs", value=int(r['h_start']), min_value=0, max_value=23, key=f"bdhs_{i}", label_visibility="collapsed")
        bdrows[i]['h_end']   = c5.number_input("he", value=int(r['h_end']),   min_value=0, max_value=23, key=f"bdhe_{i}", label_visibility="collapsed")
        if c6.button("X", key=f"bddel_{i}"): to_del_bd.append(i)
    for idx in reversed(to_del_bd): bdrows.pop(idx)
    if st.button("+ Bloc d'achat", key="bdadd"):
        bdrows.append({'name': '', 'qty': 100.0, 'price': 180.0, 'h_start': 17, 'h_end': 21})
        st.rerun()

    if st.button("Enregistrer les Block Orders", type="primary", use_container_width=True, key="bsave"):
        # Store as supply/demand with 'block' profile flag
        valid_bs = [{'actor': r['name'], 'segment': i, 'quantity': r['qty'], 'price': r['price'],
                     'profile': f"block:{r['h_start']}-{r['h_end']}"}
                    for i, r in enumerate(bsrows) if r['name'].strip() and r['qty'] > 0]
        valid_bd = [{'actor': r['name'], 'segment': i, 'quantity': r['qty'], 'price': r['price']}
                    for i, r in enumerate(bdrows) if r['name'].strip() and r['qty'] > 0]
        if valid_bs: save_supply_offers(my_zone, my_player, valid_bs)
        if valid_bd: save_demand_bids(my_zone, my_player, valid_bd)
        st.success(f"Block orders enregistres : {len(valid_bs)} vente, {len(valid_bd)} achat.")

# ════════════════════════════════════════════════════════
# TYPE 3 : LINKED / EXCLUSIFS
# ════════════════════════════════════════════════════════
elif order_type == "Linked / Exclusifs":
    st.markdown(f'<span class="order-type-badge ot-linked">Linked Orders</span> Dependances hierarchiques et groupes exclusifs', unsafe_allow_html=True)

    col_info1, col_info2 = st.columns(2)
    col_info1.info("**Offre liee (Linked)** : un bloc enfant ne peut etre accepte que si son parent l'est. Valable cote vente ET cote achat.")
    col_info2.info("**Offre exclusive** : dans un groupe, au maximum une option peut etre acceptee. Valable cote vente ET cote achat.")

    # ── Blocs Liés ──────────────────────────────────────────────
    st.markdown("### Blocs Parent/Enfant (Linked)")
    st.caption("Chaque bloc peut etre une offre de **Vente** (production) ou d'**Achat** (demande).")

    if 'linked_rows' not in st.session_state:
        st.session_state.linked_rows = [
            {'name': 'Parent Base',   'side': 'Vente', 'qty': 300.0, 'price': 35.0, 'h_start': 0,  'h_end': 23, 'role': 'Parent', 'parent_ref': ''},
            {'name': 'Enfant Extras', 'side': 'Vente', 'qty': 150.0, 'price': 45.0, 'h_start': 8,  'h_end': 20, 'role': 'Enfant', 'parent_ref': 'Parent Base'},
        ]
    lrows = st.session_state.linked_rows

    # Headers
    hcols = st.columns([2.5, 1.2, 1.8, 1.8, 1, 1, 2, 1])
    for col, lbl in zip(hcols, ["Nom du bloc", "Vente/Achat", "MW", "EUR/MWh", "H deb", "H fin", "Parent (si enfant)", ""]):
        col.markdown(f"<small style='color:#4a3aaa;font-weight:700;text-transform:uppercase;font-size:0.68rem;'>{lbl}</small>", unsafe_allow_html=True)

    to_del_l = []
    parent_names = [r['name'] for r in lrows if r.get('role') == 'Parent'] + ['— (aucun)']
    SIDES = ['Vente', 'Achat']

    for i, r in enumerate(lrows):
        c1,c2,c3,c4,c5,c6,c7,c8 = st.columns([2.5, 1.2, 1.8, 1.8, 1, 1, 2, 1])
        lrows[i]['name']    = c1.text_input("n", value=r['name'], key=f"ln_{i}", label_visibility="collapsed", placeholder="Nom du bloc")
        side_idx = SIDES.index(r.get('side', 'Vente')) if r.get('side', 'Vente') in SIDES else 0
        lrows[i]['side']    = c2.selectbox("s", SIDES, index=side_idx, key=f"lside_{i}", label_visibility="collapsed")
        lrows[i]['qty']     = c3.number_input("q", value=float(r['qty']), min_value=0.0, step=10.0, key=f"lq_{i}", label_visibility="collapsed")
        price_label = "Prix offre" if lrows[i]['side'] == 'Vente' else "Prix max"
        lrows[i]['price']   = c4.number_input(price_label, value=float(r['price']), min_value=0.0, max_value=500.0, step=1.0, key=f"lp_{i}", label_visibility="collapsed")
        lrows[i]['h_start'] = c5.number_input("hs", value=int(r['h_start']), min_value=0, max_value=23, key=f"lhs_{i}", label_visibility="collapsed")
        lrows[i]['h_end']   = c6.number_input("he", value=int(r['h_end']),   min_value=0, max_value=23, key=f"lhe_{i}", label_visibility="collapsed")
        cur_par = r.get('parent_ref', '— (aucun)')
        par_idx = parent_names.index(cur_par) if cur_par in parent_names else len(parent_names)-1
        lrows[i]['parent_ref'] = c7.selectbox("par", parent_names, index=par_idx, key=f"lpar_{i}", label_visibility="collapsed")
        lrows[i]['role'] = 'Parent' if lrows[i]['parent_ref'] == '— (aucun)' else 'Enfant'
        if c8.button("X", key=f"ldel_{i}"): to_del_l.append(i)

    for idx in reversed(to_del_l): lrows.pop(idx)

    la, lb = st.columns([1, 1])
    if la.button("+ Bloc parent (nouveau)", key="ladd_p", use_container_width=True):
        lrows.append({'name': '', 'side': 'Vente', 'qty': 200.0, 'price': 35.0, 'h_start': 0, 'h_end': 23, 'role': 'Parent', 'parent_ref': '— (aucun)'})
        st.rerun()
    if lb.button("+ Bloc enfant (conditionnel)", key="ladd_c", use_container_width=True):
        lrows.append({'name': '', 'side': 'Vente', 'qty': 100.0, 'price': 50.0, 'h_start': 8, 'h_end': 20, 'role': 'Enfant', 'parent_ref': '— (aucun)'})
        st.rerun()

    # ── Groupe Exclusif ──────────────────────────────────────────
    st.markdown("### Groupe Exclusif")
    st.caption("Au maximum **une seule option** sera retenue par le solveur. Chaque option peut etre Vente ou Achat.")

    if 'excl_rows' not in st.session_state:
        st.session_state.excl_rows = [
            {'name': 'Option A', 'side': 'Vente', 'qty': 250.0, 'price': 40.0, 'h_start': 8, 'h_end': 17},
            {'name': 'Option B', 'side': 'Vente', 'qty': 400.0, 'price': 48.0, 'h_start': 6, 'h_end': 21},
        ]
    erows = st.session_state.excl_rows

    # Headers
    ehcols = st.columns([2.5, 1.2, 1.8, 1.8, 1, 1, 1])
    for col, lbl in zip(ehcols, ["Nom de l'option", "Vente/Achat", "MW", "EUR/MWh", "H deb", "H fin", ""]):
        col.markdown(f"<small style='color:#e86c1a;font-weight:700;text-transform:uppercase;font-size:0.68rem;'>{lbl}</small>", unsafe_allow_html=True)

    to_del_e = []
    for i, r in enumerate(erows):
        c1,c2,c3,c4,c5,c6,c7 = st.columns([2.5, 1.2, 1.8, 1.8, 1, 1, 1])
        erows[i]['name']    = c1.text_input("n", value=r['name'], key=f"en_{i}", label_visibility="collapsed", placeholder="Nom option")
        eside_idx = SIDES.index(r.get('side','Vente')) if r.get('side','Vente') in SIDES else 0
        erows[i]['side']    = c2.selectbox("s", SIDES, index=eside_idx, key=f"eside_{i}", label_visibility="collapsed")
        erows[i]['qty']     = c3.number_input("q", value=float(r['qty']), min_value=0.0, step=10.0, key=f"eq_{i}", label_visibility="collapsed")
        erows[i]['price']   = c4.number_input("p", value=float(r['price']), min_value=0.0, max_value=500.0, step=1.0, key=f"ep_{i}", label_visibility="collapsed")
        erows[i]['h_start'] = c5.number_input("hs", value=int(r['h_start']), min_value=0, max_value=23, key=f"ehs_{i}", label_visibility="collapsed")
        erows[i]['h_end']   = c6.number_input("he", value=int(r['h_end']),   min_value=0, max_value=23, key=f"ehe_{i}", label_visibility="collapsed")
        if c7.button("X", key=f"edel_{i}"): to_del_e.append(i)

    for idx in reversed(to_del_e): erows.pop(idx)

    if st.button("+ Ajouter une option exclusive", key="eadd", use_container_width=False):
        erows.append({'name': f'Option {chr(65+len(erows))}', 'side': 'Vente', 'qty': 200.0, 'price': 45.0, 'h_start': 8, 'h_end': 20})
        st.rerun()

    # ── Enregistrement ───────────────────────────────────────────
    st.markdown("---")
    if st.button("Enregistrer Linked + Exclusifs", type="primary", use_container_width=True, key="lsave"):
        supply_l, demand_l = [], []
        supply_e, demand_e = [], []

        for i, r in enumerate(lrows):
            if not r['name'].strip() or r['qty'] <= 0:
                continue
            entry = {'actor': r['name'], 'segment': i, 'quantity': r['qty'], 'price': r['price'],
                     'profile': f"linked:{r.get('parent_ref','')}: {r['h_start']}-{r['h_end']}"}
            if r['side'] == 'Vente':
                supply_l.append(entry)
            else:
                demand_l.append({'actor': r['name'], 'segment': i, 'quantity': r['qty'], 'price': r['price']})

        for i, r in enumerate(erows):
            if not r['name'].strip() or r['qty'] <= 0:
                continue
            entry_s = {'actor': r['name'], 'segment': i+100, 'quantity': r['qty'], 'price': r['price'],
                       'profile': f"exclusive:{r['h_start']}-{r['h_end']}"}
            entry_d = {'actor': r['name'], 'segment': i+100, 'quantity': r['qty'], 'price': r['price']}
            if r['side'] == 'Vente':
                supply_e.append(entry_s)
            else:
                demand_e.append(entry_d)

        all_supply = supply_l + supply_e
        all_demand = demand_l + demand_e

        if all_supply: save_supply_offers(my_zone, my_player, all_supply)
        if all_demand: save_demand_bids(my_zone, my_player, all_demand)

        ns = len(all_supply); nd = len(all_demand)
        if ns + nd > 0:
            st.success(f"Enregistre : {ns} offres de vente, {nd} offres d'achat (linked + exclusifs).")
        else:
            st.error("Aucun bloc valide. Verifiez les noms et quantites.")

