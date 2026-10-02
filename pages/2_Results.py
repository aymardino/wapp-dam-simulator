"""
Page 2 — Résultats du clearing : prix, flux, dispatch, ordres bloc, résultat du trader, analyse, tableaux.
"""
import json
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from engine import get_results, get_session, ZONES, ZONE_COLORS
from ui_common import inject_css, header, lang_selector, t, currency, price_unit, money

inject_css()
with st.sidebar:
    lang_selector()

PLOTLY_LAYOUT = dict(
    template='plotly_white',
    paper_bgcolor='rgba(255,255,255,0)',
    plot_bgcolor='rgba(248,249,250,0.8)',
    font=dict(family='Inter, sans-serif', color='#1a1f1a', size=12),
    title_font=dict(family='Barlow Condensed, sans-serif', size=16, color='#1a6b3a'),
    legend=dict(bgcolor='rgba(255,255,255,0.9)', bordercolor='#b8ddc8', borderwidth=1),
    margin=dict(l=40, r=20, t=60, b=40),
)
PROFILE_COLORS = {'solar': '#f1c40f', 'hydro': '#3498db', 'baseload': '#2ecc71', 'flat': '#9b59b6',
                  'peaker': '#e74c3c', 'custom': '#95a5a6', 'block': '#1a6b3a'}
STATUS_LABEL = {'OK': 'OK', 'PRB': 'PRB', 'PAB': 'PAB', 'inactive': '—'}

header(t('results_title'), t('results_subtitle'))
auto_refresh = st.toggle(t('auto_refresh'), value=False)


def render():
    results = get_results()
    if results is None:
        st.info(t('no_results'))
        st.markdown(t('wait_admin'))
        return

    prices, flows, dispatch, summary = results['prices'], results['flows'], results['dispatch'], results['summary']
    hours = [int(h) for h in summary.get('hours', range(summary.get('horizon', 24)))]
    n = len(hours)
    unit = price_unit()
    hlabels = [f"H{h:02d}" for h in hours]
    zones_info = summary.get('zones', {})
    lines_info = summary.get('lines', {})
    diag = summary.get('diagnostics', {})

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(t('kpi_total_welfare'), money(summary['welfare'], millions=True))
    c2.metric(t('kpi_volume'), f"{summary['volume'] / 1000:.1f} GWh")
    c3.metric(t('kpi_time'), f"{summary['elapsed']} s")
    c4.metric(t('kpi_solver'), summary.get('solver', '—'))
    c5.metric(t('kpi_hours'), f"{n} h" if n > 1 else hlabels[0])
    st.markdown("---")

    tabs = st.tabs([t('tab_prices'), t('tab_flows'), t('tab_dispatch'), t('tab_blocks_res'),
                    t('tab_mine'), t('tab_analysis'), t('tab_tables')])

    # ── Prix ──────────────────────────────────────────────────────
    with tabs[0]:
        if n == 1:
            h = str(hours[0])
            zl = [z for z in ZONES if z in prices]
            vals = [prices[z].get(h, 0) for z in zl]
            fig = go.Figure(go.Bar(x=zl, y=vals, marker_color=[ZONE_COLORS.get(z, '#888') for z in zl],
                                   text=[f"{p:.0f}" for p in vals], textposition='outside'))
            fig.update_layout(title=t('prices_chart', unit=unit), xaxis_title=t('zone'), yaxis_title=unit, height=420, **PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
        else:
            fig = go.Figure()
            for z in ZONES:
                if z not in prices:
                    continue
                fig.add_trace(go.Scatter(x=hours, y=[prices[z].get(str(h), 0) for h in hours], name=z, mode='lines',
                                         line=dict(color=ZONE_COLORS.get(z, '#888'), width=2),
                                         hovertemplate=f"<b>{z}</b><br>%{{x}}h : %{{y:.1f}} {unit}<extra></extra>"))
            fig.update_layout(title=t('prices_hourly', unit=unit), xaxis_title=t('hour'), yaxis_title=unit, height=480, **PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
            zl = [z for z in ZONES if z in prices]
            zvals = [[prices[z].get(str(h), 0) for z in zl] for h in hours]
            fig_hm = go.Figure(go.Heatmap(z=zvals, x=zl, y=hlabels, colorscale='YlOrRd',
                                          text=[[f"{v:.0f}" for v in row] for row in zvals], texttemplate="%{text}",
                                          textfont=dict(size=9), colorbar=dict(title=unit)))
            fig_hm.update_layout(title=t('heatmap'), height=600, **PLOTLY_LAYOUT)
            st.plotly_chart(fig_hm, use_container_width=True)

        no_trade = [z for z, zi in zones_info.items() if zi.get('no_trade_hours')]
        if no_trade:
            st.caption(t('no_trade_note', zones=', '.join(no_trade)))

        st.markdown(f"#### {t('net_positions')}")
        net_pos = summary.get('net_pos', {})
        sz = sorted(net_pos, key=lambda z: -net_pos[z])
        nv = [net_pos[z] for z in sz]
        fig_net = go.Figure(go.Bar(x=sz, y=nv, marker_color=['#3dba74' if v > 0 else '#e05260' for v in nv],
                                   text=[f"{v:+.0f}" for v in nv], textposition='outside'))
        fig_net.add_hline(y=0, line_color='#8a9baa', line_dash='dash')
        fig_net.update_layout(title=t('net_position_chart'), xaxis_title=t('zone'), yaxis_title="MWh", height=380, **PLOTLY_LAYOUT)
        st.plotly_chart(fig_net, use_container_width=True)

    # ── Flux ──────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown(f"#### {t('flows_title')}")
        rows = []
        for key, tv in flows.items():
            li = lines_info.get(key, {})
            ntc = li.get('ntc') or 1
            avg = sum(tv.values()) / len(tv) if tv else 0
            rows.append({t('line'): key, t('avg_flow'): round(avg, 1),
                         t('direction'): '→' if avg >= 0 else '←',
                         t('ntc_mw'): li.get('ntc', '—'),
                         t('saturation'): round(100 * abs(avg) / ntc, 1) if ntc else 0.0,
                         t('saturated_hours'): li.get('saturated_hours', 0),
                         f"{t('congestion_rent')} ({currency()})": li.get('congestion_rent', 0.0)})
        df_fl = pd.DataFrame(rows).sort_values(t('avg_flow'), key=lambda s: -s.abs())
        sig = df_fl[df_fl[t('avg_flow')].abs() > 5]
        if len(sig):
            st.dataframe(sig, use_container_width=True, hide_index=True,
                         column_config={t('saturation'): st.column_config.ProgressColumn(format="%.0f %%", min_value=0, max_value=100)})
            fig_fl = go.Figure(go.Bar(x=sig[t('line')], y=sig[t('avg_flow')],
                                      marker_color=['#3dba74' if v > 0 else '#e05260' for v in sig[t('avg_flow')]],
                                      text=[f"{v:+.0f} MW" for v in sig[t('avg_flow')]], textposition='outside'))
            fig_fl.add_hline(y=0, line_color='#8a9baa')
            fig_fl.update_layout(title=t('flows_chart'), height=420, xaxis_tickangle=-45, **PLOTLY_LAYOUT)
            st.plotly_chart(fig_fl, use_container_width=True)
        else:
            st.info(t('no_flow'))
        if n > 1:
            st.markdown(f"#### {t('flows_24h')}")
            fig_fc = go.Figure()
            for corr in ['NGA->BEN', 'GHA->CIV', 'CIV->LBR', 'SEN->MLI', 'GHA->BFA', 'CIV->BFA']:
                if corr in flows:
                    fig_fc.add_trace(go.Scatter(x=hours, y=[flows[corr].get(str(h), 0) for h in hours], name=corr, mode='lines', line=dict(width=2)))
            fig_fc.add_hline(y=0, line_color='#8a9baa', line_dash='dash')
            fig_fc.update_layout(title=t('flows_corridors'), xaxis_title=t('hour'), yaxis_title="MW", height=380, **PLOTLY_LAYOUT)
            st.plotly_chart(fig_fc, use_container_width=True)

    # ── Dispatch ──────────────────────────────────────────────────
    with tabs[2]:
        st.markdown(f"#### {t('dispatch_title')}")
        order = ['solar', 'hydro', 'baseload', 'flat', 'custom', 'peaker', 'block']
        if n > 1:
            fig_d = go.Figure()
            for prof in order:
                if prof in dispatch and any(v > 0 for v in dispatch[prof]):
                    fig_d.add_trace(go.Bar(x=hours, y=dispatch[prof], name=prof.capitalize(), marker_color=PROFILE_COLORS.get(prof, '#888')))
            if 'demand' in dispatch:
                fig_d.add_trace(go.Scatter(x=hours, y=dispatch['demand'], name=t('demand_accepted'), mode='lines+markers',
                                           line=dict(color='#1a1f1a', width=2, dash='dot'), marker=dict(size=5, color='#1a1f1a')))
            fig_d.update_layout(barmode='stack', title=t('dispatch_chart'), xaxis_title=t('hour'), yaxis_title="MW", height=480, **PLOTLY_LAYOUT)
            st.plotly_chart(fig_d, use_container_width=True)
        else:
            labels = [p.capitalize() for p in order if p in dispatch and dispatch[p][0] > 0]
            values = [dispatch[p][0] for p in order if p in dispatch and dispatch[p][0] > 0]
            colors = [PROFILE_COLORS[p] for p in order if p in dispatch and dispatch[p][0] > 0]
            if values:
                fig_pie = go.Figure(go.Pie(labels=labels, values=values, marker_colors=colors, hole=0.4, textinfo='label+percent'))
                fig_pie.update_layout(title=t('mix_chart'), height=400, **PLOTLY_LAYOUT)
                st.plotly_chart(fig_pie, use_container_width=True)

    # ── Ordres bloc ───────────────────────────────────────────────
    with tabs[3]:
        blocks = summary.get('blocks', [])
        if not blocks:
            st.info(t('blocks_none'))
        else:
            df_b = pd.DataFrame([{
                t('zone'): b['zone'], t('trader'): b.get('player', ''), t('block_name'): b['name'],
                t('side'): t('sell') if b['side'] == 'S' else t('buy'), t('mw'): b['quantity'], unit: b['price'],
                t('hours_col'): f"H{b['hours'][0]:02d}–H{b['hours'][-1]:02d}" if b['hours'] else '—',
                t('accepted'): t('yes') if b['accepted'] else t('no'),
                f"{t('avg_price')} ({unit})": b.get('avg_price'),
                f"{t('surplus_if_acc')} ({currency()})": b.get('surplus_if_accepted', 0.0),
                t('status'): STATUS_LABEL.get(b['status'], b['status']),
            } for b in blocks])
            st.dataframe(df_b, use_container_width=True, hide_index=True)
            st.markdown(t('blocks_explain'))
            fig_g = go.Figure()
            for b in blocks:
                if not b['hours']:
                    continue
                acc = b['accepted']
                fig_g.add_trace(go.Bar(x=[b['hours'][-1] - b['hours'][0] + 1], y=[f"{b['zone']} · {b['name']}"], base=[b['hours'][0]],
                                       orientation='h', marker=dict(color='#1a6b3a' if acc else 'rgba(160,160,160,0.5)'),
                                       text=[f"{b['quantity']:.0f} MW @ {b['price']:.0f} · {STATUS_LABEL.get(b['status'], '')}"],
                                       textposition='inside', showlegend=False))
            fig_g.update_layout(height=120 + 30 * len(blocks), xaxis=dict(range=[-0.5, 23.5], dtick=1, title=t('hour')), **PLOTLY_LAYOUT)
            st.plotly_chart(fig_g, use_container_width=True)
        mics = summary.get('mic', [])
        st.markdown(f"#### {t('mic_results')}")
        if not mics:
            st.info(t('no_mic'))
        else:
            df_mic = pd.DataFrame([{
                t('zone'): m['zone'], t('trader'): m.get('player', ''), t('actor'): m['actor'],
                f"{t('fixed_term')} ({currency()})": m['fixed_term'], t('variable_term'): m['variable_term'],
                t('accepted_mwh'): m['accepted_mwh'], f"{t('income')} ({currency()})": m['income'],
                f"{t('required')} ({currency()})": m['required'],
                t('status'): t('withdrawn') if m['withdrawn'] else (t('satisfied') if m['satisfied'] else '—'),
            } for m in mics])
            st.dataframe(df_mic, use_container_width=True, hide_index=True)
            st.caption(t('mic_explain'))

    # ── Mon résultat ──────────────────────────────────────────────
    with tabs[4]:
        if 'my_zone' not in st.session_state:
            st.info(t('mine_login'))
        else:
            mz, mp_ = st.session_state['my_zone'], st.session_state['my_player']
            mine = [a for a in summary.get('actors', []) if a['zone'] == mz and a['player'] == mp_]
            mine_blocks = [b for b in blocks if b['zone'] == mz and b.get('player') == mp_] if summary.get('blocks') else []
            if not mine:
                st.info(t('mine_none', player=mp_, zone=mz))
            else:
                st.markdown(f"#### {t('mine_title', player=mp_, zone=mz)}")
                for side in ('S', 'D'):
                    part = [a for a in mine if a['side'] == side]
                    if not part:
                        continue
                    offered = sum(a['offered_mwh'] for a in part); accepted = sum(a['accepted_mwh'] for a in part)
                    money_ = sum(a['money'] for a in part); surplus = sum(a['surplus'] for a in part)
                    st.markdown(f"**{t('sell') if side == 'S' else t('buy')}**")
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric(t('accepted_mwh'), f"{accepted:,.0f} / {offered:,.0f}".replace(',', ' '))
                    k2.metric(t('acceptance'), f"{(100 * accepted / offered) if offered else 0:.0f} %")
                    k3.metric(t('revenue') if side == 'S' else t('payment'), money(money_))
                    k4.metric(t('surplus'), money(surplus))
                df_m = pd.DataFrame([{
                    t('actor'): a['actor'] + (f" ({t('status_withdrawn')})" if a.get('status') == 'withdrawn_mic' else ''),
                    t('side'): t('sell') if a['side'] == 'S' else t('buy'),
                    t('offered_mwh'): a['offered_mwh'], t('accepted_mwh'): a['accepted_mwh'],
                    t('acceptance'): a['acceptance_pct'], f"{t('avg_price')} ({unit})": a['avg_price'],
                    f"{t('surplus')} ({currency()})": a['surplus'],
                } for a in mine])
                st.dataframe(df_m, use_container_width=True, hide_index=True,
                             column_config={t('acceptance'): st.column_config.ProgressColumn(format="%.0f %%", min_value=0, max_value=100)})
                rejected = [(a['actor'], r) for a in mine for r in a.get('rejected', [])]
                if rejected:
                    st.markdown(f"**{t('rejected_orders')}**")
                    st.dataframe(pd.DataFrame([{t('actor'): act, t('segment'): r['segment'], t('mw'): r['quantity'], unit: r['price']}
                                               for act, r in rejected]), use_container_width=True, hide_index=True)
                    st.caption(t('why_rejected'))
                st.markdown(f"**{t('zone_prices_mine', unit=unit)}**")
                st.line_chart(pd.DataFrame({mz: [prices[mz].get(str(h), 0) for h in hours]}, index=hlabels))

    # ── Analyse ───────────────────────────────────────────────────
    with tabs[5]:
        st.markdown(f"#### {t('analysis_zones')}")
        if zones_info:
            df_z = pd.DataFrame([{
                t('zone'): z, t('generation_mwh'): zi['generation_mwh'], t('load_mwh'): zi['load_mwh'],
                t('net_mwh'): zi['net_position'], f"{t('avg_price')} ({unit})": zi['avg_price'],
                f"{t('consumer_surplus')} ({currency()})": zi['consumer_surplus'],
                f"{t('producer_surplus_fr')} ({currency()})": zi['producer_surplus'],
                t('no_trade_hours'): len(zi.get('no_trade_hours', [])),
            } for z, zi in zones_info.items()])
            st.dataframe(df_z, use_container_width=True, hide_index=True)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric(t('consumer_surplus'), money(summary.get('consumer_surplus', 0)))
        k2.metric(t('producer_surplus_fr'), money(summary.get('producer_surplus', 0)))
        k3.metric(t('congestion_rent'), money(summary.get('congestion_rent', 0)))
        k4.metric(t('kpi_total_welfare'), money(summary['welfare']))
        st.caption(t('welfare_identity') + " · " + t('identity_gap', gap=money(diag.get('welfare_identity_gap', 0))))
        st.markdown(f"#### {t('analysis_lines')}")
        if lines_info:
            df_l = pd.DataFrame([{t('line'): k, t('ntc_mw'): li['ntc'], t('avg_flow'): li['avg_flow'],
                                  t('saturated_hours'): li['saturated_hours'],
                                  f"{t('congestion_rent')} ({currency()})": li['congestion_rent']} for k, li in lines_info.items()])
            st.dataframe(df_l.sort_values(f"{t('congestion_rent')} ({currency()})", ascending=False), use_container_width=True, hide_index=True)
        st.markdown(f"#### {t('checks_title')}")
        ok = lambda cond: "✅" if cond else "⚠️"
        st.markdown(f"{ok(diag.get('pro', 0) == 0)} {t('check_pro', n=diag.get('pro', '—'))}")
        st.markdown(f"{ok(diag.get('pao', 0) == 0)} {t('check_pao', n=diag.get('pao', '—'))}")
        st.markdown(f"{ok(diag.get('unsaturated_price_gaps', 0) == 0)} {t('check_gaps', n=diag.get('unsaturated_price_gaps', '—'))}")
        st.markdown(f"{ok(diag.get('max_violation', 0) <= 0.5)} {t('check_max', v=diag.get('max_violation', '—'), unit=unit)}")
        st.markdown(f"{ok(diag.get('tie_break') == 'exact')} {t('check_tie', mode=diag.get('tie_break', '—'))}")
        st.markdown(f"ℹ️ {t('check_pricing', mode=diag.get('pricing_mode', '—'))}")
        st.markdown(f"ℹ️ {t('check_tie_rule', rule=diag.get('tie_rule', '—'), n=diag.get('tie_groups_adjusted', 0))}")
        if summary.get('n_mic'):
            st.markdown(f"ℹ️ {t('check_mic', n=diag.get('mic_iterations', 1), names=', '.join(diag.get('mic_withdrawn') or ['—']))}")
        if summary.get('n_blocks'):
            st.markdown(f"ℹ️ {t('check_pab', n=diag.get('pab_iterations', 1), fixed=diag.get('blocks_fixed') or '—')}")
            if diag.get('prb'):
                st.markdown(f"ℹ️ {t('check_prb', names=', '.join(diag['prb']))}")
        if diag.get('notes'):
            with st.expander(t('notes')):
                for note in diag['notes']:
                    st.markdown(f"- {note}")
        with st.expander(t('rules_title')):
            st.json(summary.get('rules', {}))

    # ── Tableaux ──────────────────────────────────────────────────
    with tabs[6]:
        st.markdown(f"#### {t('prices_table')}")
        pt = {t('hour'): hlabels}
        for z in ZONES:
            if z in prices:
                pt[z] = [prices[z].get(str(h)) for h in hours]
        df_p = pd.DataFrame(pt)
        st.dataframe(df_p, use_container_width=True, hide_index=True, height=min(420, 40 + 35 * n))
        st.markdown(f"#### {t('flows_table')}")
        ft = {t('hour'): hlabels}
        for key, tv in flows.items():
            vals = [tv.get(str(h), 0) for h in hours]
            if any(abs(v) > 1 for v in vals):
                ft[key] = [f"{v:+.0f}" for v in vals]
        st.dataframe(pd.DataFrame(ft), use_container_width=True, hide_index=True, height=min(420, 40 + 35 * n))
        st.markdown("---")
        cdl1, cdl2 = st.columns(2)
        cdl1.download_button(t('download_json'), data=json.dumps({'summary': summary, 'prices': prices, 'flows': flows, 'dispatch': dispatch}, indent=2, default=float),
                             file_name=f"wapp_clearing_{n}h.json", mime="application/json", use_container_width=True)
        cdl2.download_button(t('download_csv'), data=df_p.to_csv(index=False), file_name=f"wapp_prices_{n}h.csv", mime="text/csv", use_container_width=True)


if auto_refresh:
    st.fragment(run_every=10)(render)()
else:
    render()
