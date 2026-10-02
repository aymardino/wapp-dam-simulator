"""
Page 2 — Results
Displays clearing results: zonal prices, flows, dispatch, welfare progression.
"""
import os, base64
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from engine import get_results, get_session, ZONES, ZONE_COLORS, NTC, PAIRS

CSS_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
with open(CSS_PATH, encoding='utf-8') as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

LOGO_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'wapp_logo.png')
with open(LOGO_PATH, 'rb') as f:
    logo_b64 = base64.b64encode(f.read()).decode()

# ── Plotly dark theme ─────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    template='plotly_white',
    paper_bgcolor='rgba(255,255,255,0)',
    plot_bgcolor='rgba(248,249,250,0.8)',
    font=dict(family='Barlow, sans-serif', color='#1a1f1a', size=12),
    title_font=dict(family='Barlow Condensed, sans-serif', size=16, color='#1a6b3a'),
    legend=dict(bgcolor='rgba(255,255,255,0.9)', bordercolor='#b8ddc8', borderwidth=1),
    margin=dict(l=40, r=20, t=60, b=40),
)

ZONE_COLOR_LIST = [ZONE_COLORS.get(z, '#888') for z in ZONES]

# ── Header ────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="wapp-header">
        <img src="data:image/png;base64,{logo_b64}" height="50"/>
        <div>
            <h1>Résultats du Clearing</h1>
            <div class="subtitle">Day-Ahead Market — West African Power Pool</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Auto-refresh
auto_refresh = st.toggle("🔄 Actualisation automatique (10s)", value=False)
if auto_refresh:
    import time
    st.empty()
    time.sleep(10)
    st.rerun()

# ── Check for results ─────────────────────────────────────────────
session = get_session()
results = get_results()

if results is None:
    st.info("⏳ Aucun résultat disponible. Le clearing n'a pas encore été lancé.")
    st.markdown("Attendez que l'administrateur déclenche le clearing depuis la page **⚙️ Administration**.")
    st.stop()

prices   = results['prices']    # {zone: {str(t): price}}
flows    = results['flows']     # {"u->v": {str(t): val}}
dispatch = results['dispatch']  # {profile: [24 values]}
summary  = results['summary']
horizon  = summary.get('horizon', 24)
T        = list(range(horizon))

# ── KPI Row ───────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Welfare total",  f"{summary['welfare']/1e6:.2f} M€")
c2.metric("⚡ Volume échangé", f"{summary['volume']/1000:.1f} GWh")
c3.metric("⏱️ Temps de calcul", f"{summary['elapsed']}s")
c4.metric("🖥️ Solveur",        summary.get('solver', '—'))
c5.metric("🕐 Horizon",        f"{horizon}h")

st.markdown("---")

# ── TABS ──────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["💰 Prix Zonaux", "🔀 Flux d'Échange", "🏭 Dispatch", "📋 Tableaux"])

# ════════════════════════════════════════════════════════
# TAB 1: Zonal Prices
# ════════════════════════════════════════════════════════
with tab1:
    if horizon == 1:
        # Bar chart: one price per zone
        zone_list = [z for z in ZONES if z in prices]
        price_vals = [prices[z].get('0', 0) for z in zone_list]
        colors_bar = [ZONE_COLORS.get(z, '#888') for z in zone_list]

        fig = go.Figure(go.Bar(
            x=zone_list, y=price_vals,
            marker_color=colors_bar,
            text=[f"{p:.0f}" for p in price_vals],
            textposition='outside',
            textfont=dict(family='JetBrains Mono', color='#1a6b3a'),
        ))
        fig.update_layout(
            title="Prix Zonaux de Clearing (€/MWh)",
            xaxis_title="Zone", yaxis_title="€/MWh",
            height=420, **PLOTLY_LAYOUT
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        # Line chart: 24h prices per zone
        fig = go.Figure()
        for z in ZONES:
            if z not in prices:
                continue
            y = [prices[z].get(str(t), 0) for t in T]
            fig.add_trace(go.Scatter(
                x=T, y=y, name=z, mode='lines',
                line=dict(color=ZONE_COLORS.get(z, '#888'), width=2),
                hovertemplate=f"<b>{z}</b><br>Heure %{{x}}h : %{{y:.1f}} €/MWh<extra></extra>"
            ))
        fig.update_layout(
            title="Prix Zonaux Horaires (€/MWh)",
            xaxis_title="Heure", yaxis_title="€/MWh",
            height=480, **PLOTLY_LAYOUT
        )
        st.plotly_chart(fig, use_container_width=True)

        # Heatmap
        st.markdown("#### 🌡️ Heatmap Prix (Zone × Heure)")
        zone_list = [z for z in ZONES if z in prices]
        z_vals = [[prices[z].get(str(t), 0) for z in zone_list] for t in T]
        text_vals = [[f"{prices[z].get(str(t), 0):.0f}" for z in zone_list] for t in T]

        fig_hm = go.Figure(go.Heatmap(
            z=z_vals, x=zone_list, y=[f"H{t:02d}" for t in T],
            colorscale='YlOrRd',
            text=text_vals, texttemplate="%{text}",
            textfont=dict(size=9, family='JetBrains Mono'),
            colorbar=dict(title="€/MWh"),
        ))
        fig_hm.update_layout(
            title="Heatmap des prix (€/MWh)",
            height=600, **PLOTLY_LAYOUT
        )
        st.plotly_chart(fig_hm, use_container_width=True)

    # Net positions
    st.markdown("#### 📊 Positions Nettes (Export +, Import −)")
    net_pos = summary.get('net_pos', {})
    sorted_zones = sorted(net_pos.keys(), key=lambda z: -net_pos[z])
    net_vals = [net_pos[z] for z in sorted_zones]
    colors_net = ['#3dba74' if v > 0 else '#e05260' for v in net_vals]

    fig_net = go.Figure(go.Bar(
        x=sorted_zones, y=net_vals,
        marker_color=colors_net,
        text=[f"{v:+.0f}" for v in net_vals],
        textposition='outside',
        textfont=dict(family='JetBrains Mono', color='#1a6b3a'),
    ))
    fig_net.add_hline(y=0, line_color='#8a9baa', line_dash='dash')
    fig_net.update_layout(
        title="Position Nette par Zone (MWh)",
        xaxis_title="Zone", yaxis_title="MWh",
        height=380, **PLOTLY_LAYOUT
    )
    st.plotly_chart(fig_net, use_container_width=True)

# ════════════════════════════════════════════════════════
# TAB 2: Exchange Flows
# ════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### 🔀 Flux sur les Interconnexions")

    # Average flows
    avg_flows = {}
    for key, tvals in flows.items():
        avg = sum(tvals.values()) / len(tvals) if tvals else 0
        avg_flows[key] = avg

    # Filter significant flows
    sig = {k: v for k, v in avg_flows.items() if abs(v) > 5}
    if sig:
        flow_df = pd.DataFrame([
            {
                'Interconnexion': k,
                'Flux moyen (MW)': round(v, 1),
                'Direction': '→ Export' if v > 0 else '← Import',
                'NTC (MW)': NTC.get(tuple(k.split('->')), 0),
                'Saturation (%)': round(abs(v) / NTC.get(tuple(k.split('->')), 1) * 100, 1) if NTC.get(tuple(k.split('->'))) else 0
            }
            for k, v in sorted(sig.items(), key=lambda x: -abs(x[1]))
        ])

        # Color-code saturation
        st.dataframe(
            flow_df.style.background_gradient(subset=['Saturation (%)'], cmap='YlOrRd'),
            use_container_width=True,
            hide_index=True
        )

        # Bar chart of average flows
        fig_fl = go.Figure(go.Bar(
            x=list(sig.keys()),
            y=list(sig.values()),
            marker_color=['#3dba74' if v > 0 else '#e05260' for v in sig.values()],
            text=[f"{v:+.0f} MW" for v in sig.values()],
            textposition='outside',
        ))
        fig_fl.add_hline(y=0, line_color='#8a9baa')
        fig_fl.update_layout(
            title="Flux moyens (MW) — positif = sens conventionnel",
            height=420, **PLOTLY_LAYOUT,
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_fl, use_container_width=True)
    else:
        st.info("Aucun flux significatif détecté.")

    # 24h flow evolution for key corridors
    if horizon > 1:
        st.markdown("#### ⏱️ Évolution des flux sur 24h")
        key_corridors = ['NGA->BEN', 'GHA->CIV', 'CIV->LBR', 'SEN->MLI']
        fig_fc = go.Figure()
        for corr in key_corridors:
            if corr in flows:
                y = [flows[corr].get(str(t), 0) for t in T]
                # Also check reverse
                rev = corr.split('->')[1] + '->' + corr.split('->')[0]
                if rev in flows:
                    yr = [flows[rev].get(str(t), 0) for t in T]
                    y = [y[t] - yr[t] for t in T]  # net flow
                fig_fc.add_trace(go.Scatter(
                    x=T, y=y, name=corr, mode='lines',
                    line=dict(width=2),
                    hovertemplate=f"<b>{corr}</b><br>%{{x}}h : %{{y:.0f}} MW<extra></extra>"
                ))
        fig_fc.add_hline(y=0, line_color='#8a9baa', line_dash='dash')
        fig_fc.update_layout(
            title="Flux horaires — Corridors principaux (MW)",
            xaxis_title="Heure", yaxis_title="MW",
            height=380, **PLOTLY_LAYOUT
        )
        st.plotly_chart(fig_fc, use_container_width=True)

# ════════════════════════════════════════════════════════
# TAB 3: Dispatch
# ════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### 🏭 Dispatch par Profil de Production")

    PROFILE_COLORS = {
        'solar':    '#f1c40f',
        'hydro':    '#3498db',
        'baseload': '#2ecc71',
        'peaker':   '#e74c3c',
        'flat':     '#9b59b6',
        'demand':   '#ffffff',
    }

    if horizon > 1:
        fig_d = go.Figure()
        profiles_order = ['solar', 'hydro', 'baseload', 'flat', 'peaker']
        for prof in profiles_order:
            if prof in dispatch and any(v > 0 for v in dispatch[prof]):
                fig_d.add_trace(go.Bar(
                    x=T, y=dispatch[prof],
                    name=prof.capitalize(),
                    marker_color=PROFILE_COLORS.get(prof, '#888'),
                    hovertemplate=f"<b>{prof.capitalize()}</b><br>%{{x}}h : %{{y:,.0f}} MW<extra></extra>"
                ))

        # Demand line
        if 'demand' in dispatch:
            fig_d.add_trace(go.Scatter(
                x=T, y=dispatch['demand'],
                name='Demande acceptée',
                mode='lines+markers',
                line=dict(color='white', width=2, dash='dot'),
                marker=dict(size=4),
            ))

        fig_d.update_layout(
            barmode='stack',
            title="Dispatch empilé par profil (MW)",
            xaxis_title="Heure", yaxis_title="MW",
            height=480, **PLOTLY_LAYOUT
        )
        st.plotly_chart(fig_d, use_container_width=True)
    else:
        # Single hour pie
        labels, values, colors_pie = [], [], []
        for prof in ['solar', 'hydro', 'baseload', 'flat', 'peaker']:
            if prof in dispatch and dispatch[prof][0] > 0:
                labels.append(prof.capitalize())
                values.append(dispatch[prof][0])
                colors_pie.append(PROFILE_COLORS[prof])

        if values:
            fig_pie = go.Figure(go.Pie(
                labels=labels, values=values,
                marker_colors=colors_pie,
                hole=0.4,
                textinfo='label+percent',
                textfont=dict(family='Barlow Condensed', size=14),
            ))
            fig_pie.update_layout(
                title="Mix de production accepté",
                height=400, **PLOTLY_LAYOUT
            )
            st.plotly_chart(fig_pie, use_container_width=True)

# ════════════════════════════════════════════════════════
# TAB 4: Data Tables
# ════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### 📋 Prix Zonaux — Tableau Complet")

    # Build price DataFrame
    if horizon > 1:
        price_table = {'Heure': [f"H{t:02d}" for t in T]}
        for z in ZONES:
            if z in prices:
                price_table[z] = [prices[z].get(str(t), '—') for t in T]
        df_prices = pd.DataFrame(price_table)
        st.dataframe(df_prices, use_container_width=True, hide_index=True, height=400)
    else:
        rows = []
        for z in ZONES:
            if z in prices:
                p = prices[z].get('0', '—')
                np_ = summary['net_pos'].get(z, 0)
                rows.append({'Zone': z, 'Prix (€/MWh)': p, 'Position Nette (MW)': np_})
        df_prices = pd.DataFrame(rows)
        st.dataframe(df_prices, use_container_width=True, hide_index=True)

    st.markdown("#### 🔀 Flux — Tableau Complet")
    if horizon > 1:
        flow_table = {'Heure': [f"H{t:02d}" for t in T]}
        for key, tvals in flows.items():
            vals = [tvals.get(str(t), 0) for t in T]
            if any(abs(v) > 1 for v in vals):
                flow_table[key] = [f"{v:+.0f}" for v in vals]
        df_flows = pd.DataFrame(flow_table)
        st.dataframe(df_flows, use_container_width=True, hide_index=True, height=400)

    # Download button
    st.markdown("---")
    import json
    result_json = json.dumps({
        'summary': summary,
        'prices': prices,
        'flows': flows,
        'dispatch': dispatch,
    }, indent=2)
    st.download_button(
        label="⬇️ Télécharger les résultats (JSON)",
        data=result_json,
        file_name=f"wapp_clearing_{summary.get('horizon',24)}h.json",
        mime="application/json",
        use_container_width=True,
    )
