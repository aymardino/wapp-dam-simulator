"""
Page 3 — Administration: phase, settings, rules, NTC, clearing run, order overview.
"""
import os
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from engine import (get_session, set_session, reset_market, get_all_supply, get_all_demand, get_all_blocks,
                    get_players, save_results, get_results, get_ntc, set_ntc, reset_ntc, get_all_mic,
                    run_clearing, ClearingError, ZONES, LINES, NTC, PRICING_MODES, PAB_RULES, TIE_RULES)
from engine.db import get_conn
from ui_common import inject_css, header, lang_selector, t, money, hours_label, LANGS

inject_css()
with st.sidebar:
    lang_selector()


def _admin_password():
    pwd = os.environ.get('WAPP_ADMIN_PASSWORD')
    if pwd:
        return pwd
    try:
        return st.secrets['admin_password']
    except Exception:
        return None   # no default password: the page stays locked until one is configured


header(t('admin_title'), t('admin_subtitle'))

if not st.session_state.get('admin_auth', False):
    st.markdown(f"### {t('admin_access')}")
    if not _admin_password():
        st.warning("Mot de passe administrateur non configuré : définissez la variable d'environnement WAPP_ADMIN_PASSWORD "
                   "ou la clé admin_password dans .streamlit/secrets.toml, puis relancez l'application. / "
                   "Administrator password not configured: set WAPP_ADMIN_PASSWORD or admin_password in .streamlit/secrets.toml.")
        st.stop()
    pwd = st.text_input(t('password'), type="password")
    if st.button(t('connect'), type="primary"):
        if pwd == _admin_password():
            st.session_state.admin_auth = True
            st.rerun()
        else:
            st.error(t('wrong_password'))
    st.caption(t('password_hint'))
    st.stop()

session = get_session()
players = get_players()
supply  = get_all_supply()
demand  = get_all_demand()
blocks  = get_all_blocks()
mic     = get_all_mic()
phase   = session.get('phase', 'submission')

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(t('kpi_participants'), len(players))
c2.metric(t('kpi_supply'), len(supply), t('n_zones', n=len({r['zone'] for r in supply})))
c3.metric(t('kpi_demand'), len(demand), t('n_zones', n=len({r['zone'] for r in demand})))
c4.metric(t('kpi_blocks'), len(blocks), f"{t('kpi_mic')} : {len(mic)}")
c5.metric(t('phase'), t('phase_submission') if phase == 'submission' else t('phase_cleared'))
st.markdown("---")

# ── 1. Phase ──────────────────────────────────────────────────────
st.markdown(f"## {t('market_phase')}")
cp1, cp2 = st.columns(2)
with cp1:
    label = t('phase_submission') if phase == 'submission' else t('phase_cleared')
    st.markdown(f'<div style="font-size:1.1rem;margin-bottom:12px;">{t("current_state")} <span class="phase-badge phase-{phase}">{label}</span></div>', unsafe_allow_html=True)
    if phase == 'cleared':
        st.warning(t('closed_warning'))
        if st.button(t('reopen'), type="primary", use_container_width=True):
            set_session('phase', 'submission')
            st.success(t('reopened'))
            st.rerun()
    else:
        st.success(t('open_info'))
with cp2:
    st.markdown(f"**{t('full_reset')}**")
    if st.button(t('reset_button'), use_container_width=True):
        if st.session_state.get('confirm_reset', False):
            reset_market()
            st.session_state.confirm_reset = False
            st.success(t('reset_done'))
            st.rerun()
        else:
            st.session_state.confirm_reset = True
            st.rerun()
    if st.session_state.get('confirm_reset', False):
        st.error(t('click_again'))
st.markdown("---")

# ── 2. Settings ───────────────────────────────────────────────────
st.markdown(f"## {t('parameters')}")
pa, pb, pc = st.columns(3)
with pa:
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    try:
        date_val = datetime.strptime(session.get('market_date', tomorrow), '%Y-%m-%d').date()
    except Exception:
        date_val = None
    new_date = st.date_input(t('date_input'), value=date_val)
    if st.button(t('update_date')):
        set_session('market_date', str(new_date))
        st.success(t('date_set', d=new_date))
with pb:
    h_opts = [t('horizon_1h'), t('horizon_24h')]
    new_h = st.selectbox(t('horizon_input'), h_opts, index=0 if session.get('horizon', '24') == '1' else 1)
    hour = st.number_input(t('hour_input'), min_value=0, max_value=23, value=int(session.get('hour', '19')))
    if st.button(t('update_horizon')):
        set_session('horizon', '1' if new_h == t('horizon_1h') else '24')
        set_session('hour', str(int(hour)))
        st.success(t('horizon_set', h=hours_label(get_session())))
with pc:
    cur = st.text_input(t('currency_input'), value=session.get('currency', 'USD'), max_chars=8)
    lang_default = st.selectbox(t('lang_input'), list(LANGS), index=list(LANGS).index(session.get('lang', 'fr')) if session.get('lang', 'fr') in LANGS else 0,
                                format_func=lambda k: LANGS[k])
    if st.button(t('update_display')):
        set_session('currency', cur.strip() or 'USD')
        set_session('lang', lang_default)
        st.success(t('display_set'))
st.markdown("---")

# ── 3. Clearing rules ─────────────────────────────────────────────
st.markdown(f"## {t('rules_section')}")
r1, r2, r3 = st.columns(3)
pricing_labels = {'complete': t('pricing_complete'), 'l2': t('pricing_l2')}
pab_labels = {'euphemia': t('pab_euphemia'), 'l2': t('pab_l2'), 'none': t('pab_none')}
tie_labels = {'prorata': t('tie_prorata'), 'order': t('tie_order'), 'solver': t('tie_solver')}
with r1:
    pricing_choice = st.selectbox(t('pricing_input'), list(PRICING_MODES), index=list(PRICING_MODES).index(session.get('pricing', 'complete')),
                                  format_func=lambda k: pricing_labels[k])
with r2:
    pab_choice = st.selectbox(t('pab_input'), list(PAB_RULES), index=list(PAB_RULES).index(session.get('pab_rule', 'euphemia')),
                              format_func=lambda k: pab_labels[k])
with r3:
    tie_choice = st.selectbox(t('tie_input'), list(TIE_RULES), index=list(TIE_RULES).index(session.get('tie_rule', 'prorata')),
                              format_func=lambda k: tie_labels[k])
if st.button(t('update_rules')):
    set_session('pricing', pricing_choice)
    set_session('pab_rule', pab_choice)
    set_session('tie_rule', tie_choice)
    st.success(t('rules_set'))
st.markdown("---")

# ── 4. NTC ────────────────────────────────────────────────────────
st.markdown(f"## {t('ntc_section')}")
st.caption(t('ntc_help'))
custom = get_ntc()
n_changed = sum(1 for k, v in custom.items() if abs(v - NTC.get(k, v)) > 1e-9)
if n_changed:
    st.info(t('ntc_custom_active', n=n_changed))
df_ntc = pd.DataFrame([{t('line'): f"{u}->{v}", t('ntc_default'): float(c), t('ntc_current'): float(custom.get((u, v), c))}
                       for u, v, c in LINES])
edited = st.data_editor(df_ntc, use_container_width=True, hide_index=True, disabled=[t('line'), t('ntc_default')],
                        column_config={t('ntc_current'): st.column_config.NumberColumn(min_value=0.0, step=10.0)}, key="ntc_editor")
n1, n2 = st.columns(2)
if n1.button(t('save_ntc'), use_container_width=True):
    values = {}
    for _, row in edited.iterrows():
        u, v = row[t('line')].split('->')
        values[(u, v)] = float(row[t('ntc_current')])
    set_ntc(values)
    st.success(t('ntc_saved'))
    st.rerun()
if n2.button(t('reset_ntc'), use_container_width=True):
    reset_ntc()
    st.success(t('ntc_reset'))
    st.rerun()
st.markdown("---")

# ── 5. Clearing ───────────────────────────────────────────────────
st.markdown(f"## {t('clearing_section')}")
covered = {r['zone'] for r in supply} | {r['zone'] for r in demand} | {r['zone'] for r in blocks}
missing_zones = [z for z in ZONES if z not in covered]
co1, co2 = st.columns(2)
with co1:
    st.markdown(f"**{t('zones_covered')}**")
    for z in ZONES:
        ns = sum(1 for r in supply if r['zone'] == z)
        nd = sum(1 for r in demand if r['zone'] == z)
        nb = sum(1 for r in blocks if r['zone'] == z)
        st.markdown(t('zone_line', icon="✅" if z in covered else "⚪", z=z, ns=ns, nd=nd, nb=nb))
with co2:
    st.markdown(f"**{t('missing_zones')}**")
    fill_opts = {'reference': t('fill_reference'), 'ignore': t('fill_ignore'), 'demo': t('fill_demo')}
    fill_choice = st.radio(t('fill_question'), list(fill_opts), format_func=lambda k: fill_opts[k],
                           index=0 if session.get('fill_missing', '1') == '1' else 1, key="fill_option")
    if fill_choice == 'demo':
        st.warning(t('fill_demo_warn'))
    elif missing_zones:
        if fill_choice == 'reference':
            st.info(t('fill_info', n=len(missing_zones)))
        else:
            st.warning(t('fill_partial', n=len(covered)))
    else:
        st.success(t('all_zones_ok'))

session = get_session()
hours = list(range(24)) if session.get('horizon', '24') == '24' else [int(session.get('hour', '19'))]

if st.button(t('run_clearing'), type="primary", use_container_width=True):
    with st.spinner(t('running', h=hours_label(session))):
        try:
            kwargs = dict(hours=hours, pricing=session.get('pricing', 'complete'), pab_rule=session.get('pab_rule', 'euphemia'),
                          tie_rule=session.get('tie_rule', 'prorata'))
            if fill_choice == 'demo':
                result = run_clearing(None, None, **kwargs)
            else:
                set_session('fill_missing', '1' if fill_choice == 'reference' else '0')
                result = run_clearing(supply, demand, block_rows=blocks, mic_rows=mic, fill_missing_zones=(fill_choice == 'reference'), **kwargs)
            save_results(welfare=result['welfare'], volume=result['volume'], prices=result['prices'],
                         flows=result['flows'], dispatch=result['dispatch'], summary=result['summary'])
            st.success(t('clearing_done', t=result['summary']['elapsed'], w=money(result['welfare'], millions=True),
                         v=f"{result['volume'] / 1000:.1f}"))
            st.balloons()
        except ClearingError as e:
            st.error(t('clearing_error', msg=e))
        except Exception as e:
            st.error(t('unexpected_error'))
            st.exception(e)

last = get_results()
if last:
    with st.expander(t('last_diag')):
        d = last['summary'].get('diagnostics', {})
        st.json({k: v for k, v in d.items() if k != 'notes'})
        for note in d.get('notes', []):
            st.markdown(f"- {note}")
st.markdown("---")

# ── 6. Overview ───────────────────────────────────────────────────
st.markdown(f"## {t('all_offers')}")
tab_s, tab_d, tab_b, tab_p = st.tabs([t('kpi_supply'), t('kpi_demand'), t('kpi_blocks'), t('kpi_participants')])
with tab_s:
    if supply:
        df_s = pd.DataFrame(supply)[['zone', 'player', 'actor', 'segment', 'quantity', 'price', 'profile']].copy()
        df_s.columns = [t('zone'), t('trader'), t('actor'), t('segment'), t('mw'), t('price'), t('profile')]
        st.dataframe(df_s, use_container_width=True, hide_index=True)
    else:
        st.info(t('no_supply'))
with tab_d:
    if demand:
        df_d = pd.DataFrame(demand)[['zone', 'player', 'actor', 'segment', 'quantity', 'price']].copy()
        df_d.columns = [t('zone'), t('trader'), t('buyer'), t('segment'), t('mw'), t('max_price')]
        st.dataframe(df_d, use_container_width=True, hide_index=True)
    else:
        st.info(t('no_demand'))
with tab_b:
    if blocks:
        df_b = pd.DataFrame(blocks)[['zone', 'player', 'name', 'side', 'quantity', 'price', 'h_start', 'h_end', 'parent_name', 'excl_group']].copy()
        df_b.columns = [t('zone'), t('trader'), t('block_name'), t('side'), t('mw'), t('price'), t('h_start'), t('h_end'), t('parent'), t('group')]
        st.dataframe(df_b, use_container_width=True, hide_index=True)
    else:
        st.info(t('no_block_orders'))
    st.markdown(f"**{t('mic_results')}**")
    if mic:
        df_m = pd.DataFrame(mic)[['zone', 'player', 'actor', 'fixed_term', 'variable_term']].copy()
        df_m.columns = [t('zone'), t('trader'), t('actor'), t('fixed_term'), t('variable_term')]
        st.dataframe(df_m, use_container_width=True, hide_index=True)
    else:
        st.info(t('no_mic'))
with tab_p:
    if players:
        for p in players:
            ns = sum(1 for r in supply if r['zone'] == p['zone'] and r['player'] == p['player'])
            nd = sum(1 for r in demand if r['zone'] == p['zone'] and r['player'] == p['player'])
            nb = sum(1 for r in blocks if r['zone'] == p['zone'] and r['player'] == p['player'])
            st.markdown(
                f'<div class="player-card"><div class="player-dot" style="background:{p.get("color", "#1a6b3a")};"></div>'
                f'<div><div class="player-name">{p["player"]}</div>'
                f'<div style="font-size:0.72rem;color:#8a9a8a;">{ns} / {nd} / {nb}</div></div>'
                f'<div class="player-zone">{p["zone"]}</div></div>', unsafe_allow_html=True)
    else:
        st.info(t('no_participant_admin'))

with st.expander(t('danger_zone')):
    d1, d2 = st.columns(2)
    if d1.button(t('delete_all_offers'), use_container_width=True):
        conn = get_conn()
        conn.execute("DELETE FROM supply_offers"); conn.execute("DELETE FROM demand_bids"); conn.execute("DELETE FROM block_orders")
        conn.commit(); conn.close()
        st.success(t('offers_deleted'))
    if d2.button(t('disconnect_all'), use_container_width=True):
        conn = get_conn()
        conn.execute("DELETE FROM players")
        conn.commit(); conn.close()
        st.success(t('all_disconnected'))
