"""Page 3 — Administration"""
import os, base64
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from engine import get_session, set_session, reset_market, get_all_supply, get_all_demand, get_players, save_results, ZONES, ZONE_COLORS
from engine.clearing import run_clearing
from engine.db import get_conn

CSS_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
with open(CSS_PATH, encoding='utf-8') as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

LOGO_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'wapp_logo.png')
with open(LOGO_PATH, 'rb') as f:
    logo_b64 = base64.b64encode(f.read()).decode()

ADMIN_PASSWORD = "<mot-de-passe-retire>"

st.markdown(
    f'<div class="wapp-header">'
    f'<img src="data:image/png;base64,{logo_b64}" height="50"/>'
    f'<div><h1>Administration</h1><div class="subtitle">Controle de session et lancement du clearing</div></div>'
    f'</div>', unsafe_allow_html=True)

if not st.session_state.get('admin_auth', False):
    st.markdown("### Acces Administrateur")
    pwd = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter", type="primary"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.admin_auth = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")
    st.stop()

session = get_session()
players = get_players()
supply  = get_all_supply()
demand  = get_all_demand()
phase   = session.get('phase', 'submission')

c1,c2,c3,c4 = st.columns(4)
c1.metric("Participants", len(players))
c2.metric("Offres de vente", len(supply), f"{len(set(r['zone'] for r in supply))} zones")
c3.metric("Offres d'achat", len(demand), f"{len(set(r['zone'] for r in demand))} zones")
c4.metric("Phase", "Soumission ouverte" if phase == 'submission' else "Cloture")

st.markdown("---")

# SECTION 1 : PHASE
st.markdown("## Phase du marche")
col_phase1, col_phase2 = st.columns(2)

with col_phase1:
    phase_label = "Soumission ouverte" if phase == 'submission' else "Marche cloture"
    st.markdown(f'<div style="font-size:1.1rem;margin-bottom:12px;">Etat actuel : <span class="phase-badge phase-{phase}">{phase_label}</span></div>', unsafe_allow_html=True)
    if phase == 'cleared':
        st.warning("Le marche est cloture. Les traders ne peuvent plus soumettre d'offres.")
        if st.button("Reouvrir le marche (nouvelle session)", type="primary", use_container_width=True):
            set_session('phase', 'submission')
            st.success("Marche rouvert !")
            st.rerun()
    else:
        st.success("Le marche est ouvert. Les traders peuvent soumettre leurs offres.")

with col_phase2:
    st.markdown("**Reinitialisation complete**")
    if st.button("Reinitialiser le marche (supprimer toutes les offres)", use_container_width=True):
        if st.session_state.get('confirm_reset', False):
            reset_market()
            for k in ['supply_rows','demand_rows','block_supply','block_demand','linked_rows','excl_rows']:
                st.session_state.pop(k, None)
            st.session_state.confirm_reset = False
            st.success("Marche reinitialise.")
            st.rerun()
        else:
            st.session_state.confirm_reset = True
            st.rerun()
    if st.session_state.get('confirm_reset', False):
        st.error("Cliquez a nouveau pour confirmer.")

st.markdown("---")

# SECTION 2 : PARAMETRES
st.markdown("## Parametres du marche")
col_p1, col_p2 = st.columns(2)

with col_p1:
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    current_date = session.get('market_date', tomorrow)
    try:
        date_val = datetime.strptime(current_date, '%Y-%m-%d').date()
    except Exception:
        date_val = None
    new_date = st.date_input("Date de livraison (J+1 recommande)", value=date_val)
    if st.button("Mettre a jour la date"):
        set_session('market_date', str(new_date))
        st.success(f"Date : {new_date}")

with col_p2:
    horizon_idx = 1 if session.get('horizon','24') == '24' else 0
    new_horizon = st.selectbox("Horizon de simulation", ['1 heure (test rapide)', '24 heures (day-ahead complet)'], index=horizon_idx)
    horizon_val = '1' if '1 heure' in new_horizon else '24'
    if st.button("Mettre a jour l'horizon"):
        set_session('horizon', horizon_val)
        st.success(f"Horizon : {horizon_val}h")

st.markdown("---")

# SECTION 3 : CLEARING
st.markdown("## Lancement du Clearing")

connected_zones = {r['zone'] for r in supply} | {r['zone'] for r in demand}
missing_zones   = [z for z in ZONES if z not in connected_zones]

col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    st.markdown("**Zones couvertes :**")
    for z in ZONES:
        ns = sum(1 for r in supply if r['zone']==z)
        nd = sum(1 for r in demand if r['zone']==z)
        icon = "✅" if (ns>0 or nd>0) else "⚪"
        st.markdown(f"{icon} **{z}** — {ns} vente / {nd} achat")

with col_opt2:
    st.markdown("**Zones sans soumissions :**")
    fill_option = st.radio(
        "Que faire pour les zones manquantes ?",
        options=[
            "Utiliser les donnees de reference (recommande)",
            "Ignorer ces zones (marche partiel)",
            "Tout passer en mode demonstration"
        ],
        key="fill_option"
    )
    if missing_zones:
        if "reference" in fill_option:
            st.info(f"{len(missing_zones)} zones utiliseront les donnees calibrees.")
        elif "Ignorer" in fill_option:
            st.warning(f"Seules {len(connected_zones)} zones participent.")
        else:
            st.warning("Mode demonstration complet.")
    else:
        st.success("Toutes les zones ont soumis des offres.")

horizon = int(session.get('horizon', '24'))

if st.button("Lancer le Clearing Day-Ahead", type="primary", use_container_width=True):
    with st.spinner(f"Optimisation P1 -> P1bis -> P2 — {horizon}h ..."):
        try:
            if "demonstration" in fill_option:
                result = run_clearing(None, None, horizon=horizon)
            else:
                result = run_clearing(
                    supply_rows=supply if supply else None,
                    demand_rows=demand if demand else None,
                    horizon=horizon
                )
            save_results(
                welfare=result['welfare'], volume=result['volume'],
                prices=result['prices'], flows=result['flows'],
                dispatch=result['dispatch'], summary=result['summary']
            )
            w = result['welfare']/1e6
            v = result['volume']/1000
            t = result['summary']['elapsed']
            st.success(f"Clearing termine en {t}s | Welfare = {w:.2f} M EUR | Volume = {v:.1f} GWh")
            st.balloons()
        except Exception as e:
            st.error(f"Erreur : {e}")
            st.exception(e)

st.markdown("---")

# SECTION 4 : APERCU
st.markdown("## Toutes les offres soumises")
tab_s, tab_d, tab_p = st.tabs(["Offres de Vente", "Offres d'Achat", "Participants"])

with tab_s:
    if supply:
        df_s = pd.DataFrame(supply)[['zone','player','actor','segment','quantity','price','profile']].copy()
        df_s.columns = ['Zone','Trader','Acteur','Seg.','MW','EUR/MWh','Profil']
        st.dataframe(df_s, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune offre de vente.")

with tab_d:
    if demand:
        df_d = pd.DataFrame(demand)[['zone','player','actor','segment','quantity','price']].copy()
        df_d.columns = ['Zone','Trader','Acheteur','Seg.','MW','Prix Max']
        st.dataframe(df_d, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune offre d'achat.")

with tab_p:
    if players:
        for p in players:
            color = p.get('color','#1a6b3a')
            ns = sum(1 for r in supply if r['zone']==p['zone'])
            nd = sum(1 for r in demand if r['zone']==p['zone'])
            st.markdown(
                f'<div class="player-card">'
                f'<div class="player-dot" style="background:{color};"></div>'
                f'<div><div class="player-name">{p["player"]}</div>'
                f'<div style="font-size:0.72rem;color:#8a9a8a;">{ns} vente / {nd} achat</div></div>'
                f'<div class="player-zone">{p["zone"]}</div></div>', unsafe_allow_html=True)
    else:
        st.info("Aucun participant.")

with st.expander("Zone Danger"):
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if st.button("Supprimer toutes les offres", use_container_width=True):
            conn = get_conn()
            conn.execute("DELETE FROM supply_offers")
            conn.execute("DELETE FROM demand_bids")
            conn.commit(); conn.close()
            st.success("Offres supprimees.")
    with col_d2:
        if st.button("Deconnecter tous les participants", use_container_width=True):
            conn = get_conn()
            conn.execute("DELETE FROM players")
            conn.commit(); conn.close()
            st.success("Participants deconnectes.")
    st.caption(f"Mot de passe admin : '{ADMIN_PASSWORD}' — modifiable dans pages/3_Admin.py")
