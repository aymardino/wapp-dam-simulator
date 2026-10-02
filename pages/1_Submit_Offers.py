"""
Page 1 — Order submission: stepwise segments and block orders (simple, linked, exclusive).
"""
import streamlit as st
import pandas as pd
from engine import (get_session, save_supply_offers, save_demand_bids, get_zone_supply, get_zone_demand,
                    save_block_orders, delete_block_orders, get_zone_blocks, save_mic_conditions, get_zone_mic,
                    ZONE_COLORS, PROF, P_MIN, P_MAX)
from ui_common import inject_css, header, lang_selector, t, price_unit, currency

inject_css()
with st.sidebar:
    lang_selector()

PROFILE_NAMES = ['baseload', 'hydro', 'solar', 'peaker', 'flat']
SIDES = {'S': t('sell'), 'D': t('buy')}

if 'my_zone' not in st.session_state:
    st.warning(t('login_first'))
    st.stop()

my_zone   = st.session_state['my_zone']
my_player = st.session_state['my_player']
session   = get_session()
color     = ZONE_COLORS.get(my_zone, '#1a6b3a')

header(t('submit_title'),
       f'<span class="zone-pill" style="background:{color}22;border:1.5px solid {color};color:{color};">{my_zone}</span>'
       f'&nbsp;&nbsp;{my_player}')

if session.get('phase', 'submission') == 'cleared':
    st.warning(t('market_closed'))
    st.stop()

tab_step, tab_blocks, tab_preview = st.tabs([t('tab_stepwise'), t('tab_blocks'), t('tab_preview')])


def _head(cols, labels, color='#1a6b3a'):
    for col, lbl in zip(cols, labels):
        col.markdown(f"<small style='color:{color};font-weight:700;text-transform:uppercase;font-size:0.7rem;'>{lbl}</small>",
                     unsafe_allow_html=True)


# ═══════════════════════════════ Segments ═══════════════════════════════
with tab_step:
    st.markdown(f'<span class="order-type-badge ot-stepwise">Stepwise LP</span> {t("stepwise_badge")}', unsafe_allow_html=True)
    st.markdown("")
    col_s, col_d = st.columns(2)

    with col_s:
        st.markdown(f"### {t('supply_in_zone', zone=my_zone)}")
        st.caption(t('max_segments'))
        existing_supply = [r for r in get_zone_supply(my_zone) if r['player'] == my_player]
        if existing_supply:
            st.success(t('already_submitted', n=len(existing_supply)))
        if 'supply_rows' not in st.session_state:
            st.session_state.supply_rows = [
                {'actor': r['actor'], 'segment': r['segment'], 'quantity': r['quantity'], 'price': r['price'], 'profile': r.get('profile', 'baseload')}
                for r in existing_supply] or [{'actor': '', 'segment': 0, 'quantity': 100.0, 'price': 50.0, 'profile': 'baseload'}]
        rows = st.session_state.supply_rows
        _head(st.columns([3, 1, 2, 2, 2, 1]), [t('actor'), t('segment'), t('mw'), price_unit(), t('profile'), ""])
        to_del = []
        for i, row in enumerate(rows):
            c1, c2, c3, c4, c5, c6 = st.columns([3, 1, 2, 2, 2, 1])
            rows[i]['actor']    = c1.text_input("a", value=row['actor'], key=f"sa_{i}", label_visibility="collapsed", placeholder=t('actor_ph'))
            rows[i]['segment']  = c2.number_input("s", value=int(row['segment']), min_value=0, max_value=3, key=f"ss_{i}", label_visibility="collapsed")
            rows[i]['quantity'] = c3.number_input("q", value=float(row['quantity']), min_value=0.0, step=10.0, key=f"sq_{i}", label_visibility="collapsed")
            rows[i]['price']    = c4.number_input("p", value=float(row['price']), min_value=float(P_MIN), max_value=float(P_MAX), step=1.0, key=f"sp_{i}", label_visibility="collapsed")
            prof = row.get('profile', 'baseload')
            rows[i]['profile']  = c5.selectbox("pr", PROFILE_NAMES, index=PROFILE_NAMES.index(prof) if prof in PROFILE_NAMES else 0, key=f"spr_{i}", label_visibility="collapsed")
            if c6.button("✕", key=f"sdel_{i}"):
                to_del.append(i)
        for idx in reversed(to_del):
            rows.pop(idx)
        ca, cb = st.columns([1, 2])
        if ca.button(t('add_segment'), use_container_width=True, key="sadd"):
            rows.append({'actor': rows[-1]['actor'] if rows else '', 'segment': min(len(rows), 3), 'quantity': 100.0, 'price': 80.0, 'profile': 'baseload'})
            st.rerun()
        if cb.button(t('save_supply'), type="primary", use_container_width=True, key="ssave"):
            valid = [r for r in rows if r['actor'].strip() and r['quantity'] > 0]
            if not valid:
                st.error(t('no_valid_segment'))
            else:
                save_supply_offers(my_zone, my_player, valid)
                st.success(t('saved_supply', n=len(valid)))
                st.rerun()
        with st.expander(t('profiles_help')):
            st.markdown(t('profiles_table'))
        with st.expander(t('mic_section')):
            st.caption(t('mic_help'))
            existing_mic = get_zone_mic(my_zone, my_player)
            if 'mic_rows' not in st.session_state:
                st.session_state.mic_rows = [{'actor': m['actor'], 'fixed_term': m['fixed_term'], 'variable_term': m['variable_term']}
                                             for m in existing_mic] or [{'actor': '', 'fixed_term': 0.0, 'variable_term': 0.0}]
            mrows = st.session_state.mic_rows
            _head(st.columns([3, 2, 2, 1]), [t('actor'), f"{t('fixed_term')} ({currency()})", t('variable_term'), ""])
            to_del_m = []
            for i, r in enumerate(mrows):
                c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                mrows[i]['actor']         = c1.text_input("ma", value=r['actor'], key=f"ma_{i}", label_visibility="collapsed", placeholder=t('mic_actor_ph'))
                mrows[i]['fixed_term']    = c2.number_input("mf", value=float(r['fixed_term']), min_value=0.0, step=100.0, key=f"mf_{i}", label_visibility="collapsed")
                mrows[i]['variable_term'] = c3.number_input("mv", value=float(r['variable_term']), min_value=0.0, step=1.0, key=f"mv_{i}", label_visibility="collapsed")
                if c4.button("✕", key=f"mdel_{i}"):
                    to_del_m.append(i)
            for idx in reversed(to_del_m):
                mrows.pop(idx)
            ma, mb = st.columns([1, 2])
            if ma.button(t('add_mic'), use_container_width=True, key="madd"):
                mrows.append({'actor': '', 'fixed_term': 0.0, 'variable_term': 0.0})
                st.rerun()
            if mb.button(t('save_mic'), type="primary", use_container_width=True, key="msave"):
                valid_m = [r for r in mrows if r['actor'].strip()]
                save_mic_conditions(my_zone, my_player, valid_m)
                st.success(t('saved_mic', n=len(valid_m)))
                st.rerun()

    with col_d:
        st.markdown(f"### {t('demand_in_zone', zone=my_zone)}")
        st.caption(t('demand_help'))
        existing_demand = [r for r in get_zone_demand(my_zone) if r['player'] == my_player]
        if existing_demand:
            st.success(t('already_submitted', n=len(existing_demand)))
        if 'demand_rows' not in st.session_state:
            st.session_state.demand_rows = [
                {'actor': r['actor'], 'segment': r['segment'], 'quantity': r['quantity'], 'price': r['price']}
                for r in existing_demand] or [{'actor': '', 'segment': 0, 'quantity': 500.0, 'price': 180.0}]
        drows = st.session_state.demand_rows
        _head(st.columns([3, 1, 2, 2, 1]), [t('buyer'), t('segment'), t('mw'), f"{t('max_price')} ({price_unit()})", ""])
        to_del_d = []
        for i, row in enumerate(drows):
            c1, c2, c3, c4, c5 = st.columns([3, 1, 2, 2, 1])
            drows[i]['actor']    = c1.text_input("a", value=row['actor'], key=f"da_{i}", label_visibility="collapsed", placeholder=t('buyer_ph'))
            drows[i]['segment']  = c2.number_input("s", value=int(row['segment']), min_value=0, max_value=3, key=f"ds_{i}", label_visibility="collapsed")
            drows[i]['quantity'] = c3.number_input("q", value=float(row['quantity']), min_value=0.0, step=10.0, key=f"dq_{i}", label_visibility="collapsed")
            drows[i]['price']    = c4.number_input("p", value=float(row['price']), min_value=float(P_MIN), max_value=float(P_MAX), step=1.0, key=f"dp_{i}", label_visibility="collapsed")
            if c5.button("✕", key=f"ddel_{i}"):
                to_del_d.append(i)
        for idx in reversed(to_del_d):
            drows.pop(idx)
        da, db = st.columns([1, 2])
        if da.button(t('add_segment'), use_container_width=True, key="dadd"):
            drows.append({'actor': drows[-1]['actor'] if drows else '', 'segment': min(len(drows), 3), 'quantity': 200.0, 'price': 150.0})
            st.rerun()
        if db.button(t('save_demand'), type="primary", use_container_width=True, key="dsave"):
            valid_d = [r for r in drows if r['actor'].strip() and r['quantity'] > 0]
            if not valid_d:
                st.error(t('no_valid_segment'))
            else:
                save_demand_bids(my_zone, my_player, valid_d)
                st.success(t('saved_demand', n=len(valid_d)))
                st.rerun()

# ═══════════════════════════════ Blocks ══════════════════════════════
with tab_blocks:
    st.markdown(f'<span class="order-type-badge ot-block">Block orders · MILP</span> {t("blocks_badge")}', unsafe_allow_html=True)
    st.markdown(f"### {t('blocks_in_zone', zone=my_zone)}")
    existing_blocks = get_zone_blocks(my_zone, my_player)
    if existing_blocks:
        st.success(t('already_submitted', n=len(existing_blocks)))
    if 'block_rows' not in st.session_state:
        st.session_state.block_rows = [
            {'name': b['name'], 'side': b['side'], 'qty': b['quantity'], 'price': b['price'],
             'h_start': b['h_start'], 'h_end': b['h_end'], 'parent': b.get('parent_name') or '', 'group': b.get('excl_group') or ''}
            for b in existing_blocks] or [{'name': '', 'side': 'S', 'qty': 100.0, 'price': 40.0, 'h_start': 0, 'h_end': 23, 'parent': '', 'group': ''}]
    brows = st.session_state.block_rows
    widths = [2.6, 1.2, 1.4, 1.4, 1, 1, 2, 1.4, 0.7]
    _head(st.columns(widths), [t('block_name'), t('side'), t('mw'), price_unit(), t('h_start'), t('h_end'), t('parent'), t('group'), ""], color='#4a3aaa')
    to_del_b = []
    for i, r in enumerate(brows):
        c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns(widths)
        brows[i]['name']    = c1.text_input("n", value=r['name'], key=f"bn_{i}", label_visibility="collapsed", placeholder=t('block_name_ph'))
        brows[i]['side']    = c2.selectbox("s", list(SIDES), index=list(SIDES).index(r.get('side', 'S')), format_func=lambda k: SIDES[k], key=f"bs_{i}", label_visibility="collapsed")
        brows[i]['qty']     = c3.number_input("q", value=float(r['qty']), min_value=0.0, step=10.0, key=f"bq_{i}", label_visibility="collapsed")
        brows[i]['price']   = c4.number_input("p", value=float(r['price']), min_value=float(P_MIN), max_value=float(P_MAX), step=1.0, key=f"bp_{i}", label_visibility="collapsed")
        brows[i]['h_start'] = c5.number_input("hs", value=int(r['h_start']), min_value=0, max_value=23, key=f"bhs_{i}", label_visibility="collapsed")
        brows[i]['h_end']   = c6.number_input("he", value=int(r['h_end']), min_value=0, max_value=23, key=f"bhe_{i}", label_visibility="collapsed")
        others = [t('none')] + [o['name'] for j, o in enumerate(brows) if j != i and o['name'].strip()]
        cur = r.get('parent') or t('none')
        brows[i]['parent']  = c7.selectbox("par", others, index=others.index(cur) if cur in others else 0, key=f"bpar_{i}", label_visibility="collapsed")
        if brows[i]['parent'] == t('none'):
            brows[i]['parent'] = ''
        brows[i]['group']   = c8.text_input("g", value=r.get('group', ''), key=f"bg_{i}", label_visibility="collapsed", placeholder=t('group_ph'))
        if c9.button("✕", key=f"bdel_{i}"):
            to_del_b.append(i)
    for idx in reversed(to_del_b):
        brows.pop(idx)
    ba, bb, bc = st.columns([1, 2, 1])
    if ba.button(t('add_block'), use_container_width=True, key="badd"):
        brows.append({'name': '', 'side': 'S', 'qty': 100.0, 'price': 40.0, 'h_start': 8, 'h_end': 20, 'parent': '', 'group': ''})
        st.rerun()
    if bb.button(t('save_blocks'), type="primary", use_container_width=True, key="bsave"):
        valid_b = [dict(name=r['name'].strip(), side=r['side'], quantity=r['qty'], price=r['price'],
                        h_start=int(r['h_start']), h_end=int(r['h_end']),
                        parent_name=(r['parent'] or None), excl_group=(r['group'].strip() or None))
                   for r in brows if r['name'].strip() and r['qty'] > 0 and r['h_end'] >= r['h_start']]
        if not valid_b:
            st.error(t('no_valid_block'))
        else:
            save_block_orders(my_zone, my_player, valid_b)
            st.success(t('saved_blocks', n=len(valid_b)))
            st.rerun()
    if bc.button(t('delete_blocks'), use_container_width=True, key="bclear"):
        delete_block_orders(my_zone, my_player)
        st.session_state.pop('block_rows', None)
        st.success(t('blocks_deleted'))
        st.rerun()

# ═══════════════════════════════ Summary ═══════════════════════════════
with tab_preview:
    supply_data = get_zone_supply(my_zone)
    demand_data = get_zone_demand(my_zone)
    block_data  = get_zone_blocks(my_zone)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"#### {t('preview_supply')}")
        if supply_data:
            df_s = pd.DataFrame(supply_data)[['player', 'actor', 'segment', 'quantity', 'price', 'profile']]
            df_s.columns = [t('trader'), t('actor'), t('segment'), t('mw'), price_unit(), t('profile')]
            st.dataframe(df_s, use_container_width=True, hide_index=True)
            st.metric(t('total_capacity'), f"{int(df_s[t('mw')].sum()):,} MW")
        else:
            st.info(t('no_supply'))
    with c2:
        st.markdown(f"#### {t('preview_demand')}")
        if demand_data:
            df_d = pd.DataFrame(demand_data)[['player', 'actor', 'segment', 'quantity', 'price']]
            df_d.columns = [t('trader'), t('buyer'), t('segment'), t('mw'), t('max_price')]
            st.dataframe(df_d, use_container_width=True, hide_index=True)
            st.metric(t('total_demand'), f"{int(df_d[t('mw')].sum()):,} MW")
        else:
            st.info(t('no_demand'))
    st.markdown(f"#### {t('preview_blocks')}")
    if block_data:
        df_b = pd.DataFrame(block_data)
        df_b['hours'] = df_b.apply(lambda r: f"H{int(r['h_start']):02d}–H{int(r['h_end']):02d}", axis=1)
        df_b['side'] = df_b['side'].map(SIDES)
        df_b = df_b[['player', 'name', 'side', 'quantity', 'price', 'hours', 'parent_name', 'excl_group']]
        df_b.columns = [t('trader'), t('block_name'), t('side'), t('mw'), price_unit(), t('hours_col'), t('parent'), t('group')]
        st.dataframe(df_b, use_container_width=True, hide_index=True)
    else:
        st.info(t('no_blocks'))
    st.markdown(f"#### {t('mic_results')}")
    mic_data = get_zone_mic(my_zone)
    if mic_data:
        df_m = pd.DataFrame(mic_data)[['player', 'actor', 'fixed_term', 'variable_term']]
        df_m.columns = [t('trader'), t('actor'), f"{t('fixed_term')} ({currency()})", t('variable_term')]
        st.dataframe(df_m, use_container_width=True, hide_index=True)
    else:
        st.info(t('no_mic'))
