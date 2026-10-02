"""
WAPP Day-Ahead Market Simulator — page d'accueil
"""
from datetime import datetime, timedelta
import streamlit as st
from engine import get_session, set_session, get_players, register_player, get_results, ZONES, ZONE_COLORS
from engine.actors import ZONE_ACTORS, CUSTOM_SENTINEL
from ui_common import inject_css, header, logo_b64, map_b64, lang_selector, t, money, hours_label

st.set_page_config(page_title="WAPP Market Simulator", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
inject_css()

# ── Date de livraison J+1 par défaut ──────────────────────────────
session = get_session()
if session.get('market_date', '') in ('', datetime.now().strftime('%Y-%m-%d')):
    set_session('market_date', (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))
    session = get_session()

# ── Barre latérale ────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div style="text-align:center;margin-bottom:16px;"><img src="data:image/png;base64,{logo_b64()}" width="80"/></div>', unsafe_allow_html=True)
    lang_selector()
    st.markdown(f"### {t('login_title')}")
    st.markdown("---")

    zone_options = [t('select_placeholder')] + ZONES
    selected_zone = st.selectbox(t('zone_country'), zone_options, key="zone_select")

    player_name = ""
    if selected_zone != t('select_placeholder'):
        actor_list = ZONE_ACTORS.get(selected_zone, []) + [CUSTOM_SENTINEL]
        selected_actor = st.selectbox(t('organisation'), actor_list, key="actor_select")
        if selected_actor == CUSTOM_SENTINEL:
            player_name = st.text_input(t('custom_name'), placeholder=t('custom_name_ph'), key="custom_name")
        else:
            player_name = selected_actor
            st.caption(t('connected_as', name=player_name))

    if st.button(t('connect'), use_container_width=True, type="primary"):
        if selected_zone == t('select_placeholder') or not player_name.strip():
            st.error(t('select_zone_and_name'))
        else:
            register_player(selected_zone, player_name.strip())
            st.session_state['my_zone'] = selected_zone
            st.session_state['my_player'] = player_name.strip()
            st.success(t('connected_ok', name=player_name, zone=selected_zone))
            st.rerun()

    if 'my_zone' in st.session_state:
        color = ZONE_COLORS.get(st.session_state['my_zone'], '#1a6b3a')
        st.markdown(
            f'<div class="player-card" style="margin-top:12px;"><div class="player-dot" style="background:{color};"></div>'
            f'<div class="player-name">{st.session_state["my_player"]}</div>'
            f'<div class="player-zone">{st.session_state["my_zone"]}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    session = get_session()
    phase = session.get('phase', 'submission')
    phase_label = t('phase_submission') if phase == 'submission' else t('phase_cleared')
    st.markdown(f'<div><strong>{t("phase")} :</strong> <span class="phase-badge phase-{phase}">{phase_label}</span></div>', unsafe_allow_html=True)
    st.markdown(f"**{t('delivery_date')} :** {session.get('market_date', '—')}")
    st.markdown(f"**{t('horizon')} :** {hours_label(session)}")
    st.markdown("---")
    st.page_link("pages/1_Submit_Offers.py", label=t('nav_submit'), icon="📋")
    st.page_link("pages/2_Results.py", label=t('nav_results'), icon="📊")
    st.page_link("pages/3_Admin.py", label=t('nav_admin'), icon="⚙️")

# ── En-tête et indicateurs ────────────────────────────────────────
header(t('app_title'), t('app_subtitle'), height=60)

players = get_players()
results = get_results()
c1, c2, c3, c4 = st.columns(4)
c1.metric(t('kpi_countries'), len({p['zone'] for p in players}), t('kpi_zones', n=len(ZONES)))
c2.metric(t('kpi_date'), session.get('market_date', '—'))
c3.metric(t('horizon'), hours_label(session))
c4.metric(t('kpi_welfare'), money(results['welfare'], millions=True) if results else "—")

st.markdown("---")

# ── Carte et participants ─────────────────────────────────────────
col_map, col_players = st.columns([2, 1])
with col_map:
    st.markdown(f"## {t('network')}")
    st.markdown(f'<div class="map-container"><img src="data:image/png;base64,{map_b64()}" style="width:100%;max-height:480px;object-fit:contain;"/></div>', unsafe_allow_html=True)
    st.caption(t('data_disclaimer'))

with col_players:
    st.markdown(f"## {t('participants')}")
    if not players:
        st.info(t('no_participant'))
    else:
        for p in players:
            color = p.get('color', '#1a6b3a')
            st.markdown(
                f'<div class="player-card"><div class="player-dot" style="background:{color};"></div>'
                f'<div><div class="player-name">{p["player"]}</div>'
                f'<div style="font-size:0.72rem;color:#8a9a8a;">{(p["connected_at"] or "")[:16]}</div></div>'
                f'<div class="player-zone">{p["zone"]}</div></div>', unsafe_allow_html=True)
    missing = [z for z in ZONES if z not in {p['zone'] for p in players}]
    if missing:
        st.markdown(t('without_trader', zones=', '.join(missing)))
        st.caption(t('without_trader_hint'))

st.markdown("---")
st.markdown(f"## {t('how_to')}")
c1, c2, c3 = st.columns(3)
c1.markdown(t('how_1'))
c2.markdown(t('how_2'))
c3.markdown(t('how_3'))

st.markdown("---")
st.markdown(f'<div style="text-align:center;color:#8a9a8a;font-size:0.75rem;">{t("footer")}</div>', unsafe_allow_html=True)
