"""
WAPP Day-Ahead Market Simulator — Page d'accueil
"""
import os, base64
from datetime import datetime, timedelta
import streamlit as st
from engine import get_session, set_session, get_players, register_player, ZONES, ZONE_COLORS
from engine.actors import ZONE_ACTORS, CUSTOM_SENTINEL

st.set_page_config(page_title="WAPP Market Simulator", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

CSS_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'style.css')
with open(CSS_PATH, encoding='utf-8') as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def img_b64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

LOGO_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'wapp_logo.png')
MAP_PATH  = os.path.join(os.path.dirname(__file__), 'assets', 'wapp_map.png')
logo_b64  = img_b64(LOGO_PATH)
map_b64   = img_b64(MAP_PATH)

# ── Init session defaults (date J+1) ──────────────────────────────
session = get_session()
if session.get('market_date', '') == '' or session.get('market_date') == datetime.now().strftime('%Y-%m-%d'):
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    set_session('market_date', tomorrow)
    session = get_session()

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div style="text-align:center;margin-bottom:16px;"><img src="data:image/png;base64,{logo_b64}" width="80"/></div>', unsafe_allow_html=True)
    st.markdown("### Connexion Trader")
    st.markdown("---")

    zone_options = ["— Sélectionner —"] + ZONES
    selected_zone = st.selectbox("Zone / Pays", zone_options, key="zone_select")

    # Actor dropdown per zone
    player_name = ""
    if selected_zone != "— Sélectionner —":
        actor_list = ZONE_ACTORS.get(selected_zone, []) + [CUSTOM_SENTINEL]
        selected_actor = st.selectbox("Organisation", actor_list, key="actor_select")
        if selected_actor == CUSTOM_SENTINEL:
            player_name = st.text_input("Nom personnalisé", placeholder="ex: Mon Organisation", key="custom_name")
        else:
            player_name = selected_actor
            st.caption(f"Connecté en tant que : **{player_name}**")

    if st.button("Se connecter", use_container_width=True, type="primary"):
        if selected_zone == "— Sélectionner —" or not player_name.strip():
            st.error("Sélectionnez une zone et un nom.")
        else:
            register_player(selected_zone, player_name.strip())
            st.session_state['my_zone']   = selected_zone
            st.session_state['my_player'] = player_name.strip()
            st.success(f"Connecté : **{player_name}** ({selected_zone})")
            st.rerun()

    if 'my_zone' in st.session_state:
        color = ZONE_COLORS.get(st.session_state['my_zone'], '#1a6b3a')
        st.markdown(
            f'<div class="player-card" style="margin-top:12px;">'
            f'<div class="player-dot" style="background:{color};"></div>'
            f'<div class="player-name">{st.session_state["my_player"]}</div>'
            f'<div class="player-zone">{st.session_state["my_zone"]}</div>'
            f'</div>', unsafe_allow_html=True)

    st.markdown("---")
    session = get_session()
    phase = session.get('phase', 'submission')
    phase_label = "⏳ Soumission ouverte" if phase == 'submission' else "✅ Marche cloture"
    st.markdown(f'<div><strong>Phase :</strong> <span class="phase-badge phase-{phase}">{phase_label}</span></div>', unsafe_allow_html=True)
    st.markdown(f"**Date livraison :** {session.get('market_date', '—')}")
    st.markdown(f"**Horizon :** {session.get('horizon', '24')}h")
    st.markdown("---")
    st.page_link("pages/1_Submit_Offers.py", label="Soumettre Offres",  icon="📋")
    st.page_link("pages/2_Results.py",        label="Resultats",          icon="📊")
    st.page_link("pages/3_Admin.py",           label="Administration",     icon="⚙️")

# ── Header ────────────────────────────────────────────────────────
st.markdown(
    f'<div class="wapp-header">'
    f'<img src="data:image/png;base64,{logo_b64}" height="60"/>'
    f'<div><h1>WAPP Day-Ahead Market Simulator</h1>'
    f'<div class="subtitle">West African Power Pool — Outil de Formation au Marche Electrique</div></div>'
    f'</div>', unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────
players = get_players()
from engine import get_results
results = get_results()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Pays connectes", len(players), f"/ {len(ZONES)} zones")
c2.metric("Date de livraison (J+1)", session.get('market_date', '—'))
c3.metric("Horizon", f"{session.get('horizon','24')}h")
welfare_str = f"{results['welfare']/1e6:.2f} M EUR" if results else "—"
c4.metric("Welfare dernier clearing", welfare_str)

st.markdown("---")

# ── Map + Participants ────────────────────────────────────────────
col_map, col_players = st.columns([2, 1])

with col_map:
    st.markdown("## Reseau WAPP")
    st.markdown(f'<div class="map-container"><img src="data:image/png;base64,{map_b64}" style="width:100%;max-height:480px;object-fit:contain;"/></div>', unsafe_allow_html=True)

with col_players:
    st.markdown("## Participants")
    if not players:
        st.info("Aucun participant connecte. Connectez-vous via la barre laterale.")
    else:
        for p in players:
            color = p.get('color', '#1a6b3a')
            st.markdown(
                f'<div class="player-card">'
                f'<div class="player-dot" style="background:{color};"></div>'
                f'<div><div class="player-name">{p["player"]}</div>'
                f'<div style="font-size:0.72rem;color:#8a9a8a;">{p["connected_at"][:16] if p["connected_at"] else ""}</div></div>'
                f'<div class="player-zone">{p["zone"]}</div></div>', unsafe_allow_html=True)

    connected_zones = {p['zone'] for p in players}
    missing = [z for z in ZONES if z not in connected_zones]
    if missing:
        st.markdown(f"**Sans trader :** {', '.join(missing)}")
        st.caption("Ces zones utiliseront les donnees par defaut lors du clearing (configurable dans Admin).")

st.markdown("---")
st.markdown("## Comment utiliser")
c1, c2, c3 = st.columns(3)
c1.markdown("**1. Connexion**\n\nChaque participant selectionne son pays et son organisation dans la barre laterale.")
c2.markdown("**2. Soumission**\n\nVia *Soumettre Offres*, chaque trader soumet ses offres de vente/achat avec le type d'ordre souhaite.")
c3.markdown("**3. Clearing**\n\nL'administrateur lance le clearing depuis *Administration*. Les resultats s'affichent dans *Resultats*.")

st.markdown("---")
st.markdown('<div style="text-align:center;color:#8a9a8a;font-size:0.75rem;">WAPP Market Simulator — Projet MS OSE 2025 | Mines Paris-PSL x SENELEC x EPEX SPOT</div>', unsafe_allow_html=True)
