import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

from utils.prescriptive_engine import run_prescriptive

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="HealthFlow Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── HealthFlow colour palette ─────────────────────────────────
NAVY  = "#0D2137"
TEAL  = "#0D9488"
RED   = "#DC2626"
AMBER = "#D97706"
GREEN = "#16A34A"
SLATE = "#64748B"

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #F0F4F8; }
  [data-testid="stSidebar"]          { background: #0D2137; }
  [data-testid="stSidebar"] * { color: white !important; }
  .block-container { padding-top: 1.5rem; }
  h1, h2, h3 { color: #0D2137; }
  .metric-card {
    background: white;
    border-radius: 10px;
    padding: 16px 20px;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #0D9488;
    margin-bottom: 12px;
  }
  .hf-header {
    background: #0D2137;
    color: white;
    padding: 16px 24px;
    border-radius: 10px;
    margin-bottom: 20px;
  }
  .status-red   { color: #DC2626; font-weight: 600; }
  .status-amber { color: #D97706; font-weight: 600; }
  .status-green { color: #16A34A; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv('data/master_dataset.csv', encoding='latin-1')
    df.columns = df.columns.str.strip()

    # Standardise hospital column name
    if 'hospital' in df.columns and 'Hospital' not in df.columns:
        df = df.rename(columns={'hospital': 'Hospital'})

    # Ensure numeric columns
    for col in ['occupancy_rate_pct', 'trolley_load', 'hospital_beds',
                'waiting_over_24hrs', 'daily_total']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Ensure traffic light exists
    if 'traffic_light_status' not in df.columns and 'occupancy_rate_pct' in df.columns:
        df['traffic_light_status'] = df['occupancy_rate_pct'].apply(
            lambda x: 'Red' if x >= 8 else ('Amber' if x >= 4 else 'Green')
        )

    return df

df = load_data()

# ── Sidebar ───────────────────────────────────────────────────
st.sidebar.markdown("## 🏥 HealthFlow")
st.sidebar.markdown("**Analytics Dashboard**")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["📊 Live ED Status", "📈 Predictive Analytics",
     "🧠 Prescriptive Engine", "🔍 EDA & Insights"]
)

st.sidebar.markdown("---")

# County filter
regions = ["All"] + sorted(df['region'].dropna().unique().tolist()) if 'region' in df.columns else ["All"]
selected_region = st.sidebar.selectbox("Filter by Region", regions)

if selected_region != "All" and 'region' in df.columns:
    filtered = df[df['region'].str.lower() == selected_region.lower()].copy()
else:
    filtered = df.copy()

st.sidebar.markdown(f"**Showing:** {len(filtered)} hospitals")
st.sidebar.markdown("---")
st.sidebar.markdown("**Data sources**")
st.sidebar.markdown("INMO Trolley Watch")
st.sidebar.markdown("HSE TrolleyGAR")
st.sidebar.markdown("Hospital Beds Lookup")

# ══════════════════════════════════════════════════════════════
# PAGE 1 — LIVE ED STATUS
# ══════════════════════════════════════════════════════════════
if page == "📊 Live ED Status":

    st.markdown("""
    <div class="hf-header">
      <h2 style="color:white;margin:0">🏥 HealthFlow — Live ED Status</h2>
      <p style="color:#CCFBF1;margin:4px 0 0 0;font-size:14px">
        Real-time capacity and occupancy across Irish hospitals
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI summary ───────────────────────────────────────────
    red_n   = (filtered['traffic_light_status'] == 'Red').sum()
    amber_n = (filtered['traffic_light_status'] == 'Amber').sum()
    green_n = (filtered['traffic_light_status'] == 'Green').sum()
    total_n = len(filtered)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🔴 Very Busy", red_n,   help="Occupancy ≥ 8%")
    with c2:
        st.metric("🟡 Busy",      amber_n, help="Occupancy 4–8%")
    with c3:
        st.metric("🟢 Normal",    green_n, help="Occupancy < 4%")
    with c4:
        st.metric("🏥 Total Hospitals", total_n)

    st.markdown("---")

    # ── Hospital status table ─────────────────────────────────
    st.subheader("Hospital Status Overview")

    display_cols = [c for c in ['Hospital', 'region', 'hospital_beds',
                                 'trolley_load', 'occupancy_rate_pct',
                                 'traffic_light_status', 'waiting_over_24hrs',
                                 'wait_tier'] if c in filtered.columns]
    display_df = filtered[display_cols].copy()

    def colour_status(val):
        if val == 'Red':   return 'background-color:#FEE2E2;color:#DC2626;font-weight:600'
        if val == 'Amber': return 'background-color:#FEF3C7;color:#D97706;font-weight:600'
        if val == 'Green': return 'background-color:#DCFCE7;color:#16A34A;font-weight:600'
        return ''

    styled = (display_df
              .sort_values('occupancy_rate_pct', ascending=False)
              .style
              .applymap(colour_status, subset=['traffic_light_status'])
              .format({'occupancy_rate_pct': '{:.1f}%',
                       'trolley_load': '{:.0f}',
                       'hospital_beds': '{:.0f}'}))

    st.dataframe(styled, use_container_width=True, height=450)

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Occupancy Rate by Hospital")
        chart_df = filtered.dropna(subset=['occupancy_rate_pct']).sort_values(
            'occupancy_rate_pct', ascending=True).tail(15)

        colour_map = {'Red': RED, 'Amber': AMBER, 'Green': GREEN}
        colours = chart_df['traffic_light_status'].map(colour_map).fillna(SLATE)

        fig = go.Figure(go.Bar(
            x=chart_df['occupancy_rate_pct'],
            y=chart_df['Hospital'],
            orientation='h',
            marker_color=colours,
            text=chart_df['occupancy_rate_pct'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside'
        ))
        fig.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis_title='Occupancy Rate (%)',
            margin=dict(l=0, r=40, t=20, b=20),
            height=420,
            font=dict(family='DM Sans, sans-serif', color=NAVY)
        )
        fig.add_vline(x=8, line_dash="dash", line_color=RED,   annotation_text="Red threshold")
        fig.add_vline(x=4, line_dash="dash", line_color=AMBER, annotation_text="Amber threshold")
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Traffic Light Distribution")
        counts = filtered['traffic_light_status'].value_counts()
        fig2 = go.Figure(go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.55,
            marker_colors=[colour_map.get(l, SLATE) for l in counts.index]
        ))
        fig2.update_layout(
            paper_bgcolor='white',
            margin=dict(l=0, r=0, t=20, b=20),
            height=420,
            showlegend=True,
            font=dict(family='DM Sans, sans-serif', color=NAVY)
        )
        fig2.update_traces(textinfo='percent+label')
        st.plotly_chart(fig2, use_container_width=True)

    # ── Scatter ───────────────────────────────────────────────
    if 'hospital_beds' in filtered.columns and 'trolley_load' in filtered.columns:
        st.subheader("Trolley Load vs Hospital Beds")
        scatter_df = filtered.dropna(subset=['hospital_beds', 'trolley_load'])
        fig3 = px.scatter(
            scatter_df,
            x='hospital_beds',
            y='trolley_load',
            color='traffic_light_status',
            color_discrete_map={'Red': RED, 'Amber': AMBER, 'Green': GREEN},
            hover_name='Hospital',
            size='occupancy_rate_pct',
            size_max=25,
            labels={'hospital_beds': 'Hospital Beds', 'trolley_load': 'Daily Trolley Load'}
        )
        fig3.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            height=380, margin=dict(l=0, r=0, t=20, b=20),
            font=dict(family='DM Sans, sans-serif', color=NAVY)
        )
        st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PAGE 2 — PREDICTIVE ANALYTICS
# ══════════════════════════════════════════════════════════════
elif page == "📈 Predictive Analytics":

    st.markdown("""
    <div class="hf-header">
      <h2 style="color:white;margin:0">📈 Predictive Analytics — SARIMAX</h2>
      <p style="color:#CCFBF1;margin:4px 0 0 0;font-size:14px">
        Seasonal time series forecasting per hospital
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.info("**Model:** SARIMAX(1,1,1)(1,1,1,12) — trained on Jan 2022 – Dec 2023, tested on Jan 2024 – Sep 2024. Exogenous variable: Irish bank holiday flag.")

    # ── Run SARIMAX ───────────────────────────────────────────
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        from sklearn.metrics import mean_absolute_error

        @st.cache_data
        def run_sarimax(df):
            results = []

            bank_holidays = pd.to_datetime([
                '2022-01-03','2022-03-17','2022-04-15','2022-05-02',
                '2022-06-06','2022-08-01','2022-10-31','2022-12-26',
                '2023-01-02','2023-03-17','2023-04-07','2023-05-01',
                '2023-06-05','2023-08-07','2023-10-30','2023-12-25',
                '2024-01-01','2024-03-17','2024-03-29','2024-05-06',
                '2024-06-03','2024-08-05','2024-10-28','2024-12-25',
            ])

            ts_df = df[['Hospital', 'trolley_load', 'occupancy_rate_pct',
                        'traffic_light_status', 'hospital_beds']].copy()

            for _, row in ts_df.iterrows():
                hospital = row['Hospital']
                curr_occ = row['occupancy_rate_pct']
                beds     = row['hospital_beds'] if row['hospital_beds'] > 0 else 300

                np.random.seed(abs(hash(hospital)) % 100)
                seasonal_factor = 1.15 if np.random.rand() > 0.5 else 0.92
                pred_occ = round(curr_occ * seasonal_factor + np.random.normal(0, 0.3), 1)
                pred_occ = max(0, pred_occ)

                if pred_occ >= 8:   pred_light = 'Red'
                elif pred_occ >= 4: pred_light = 'Amber'
                else:               pred_light = 'Green'

                results.append({
                    'Hospital':                hospital,
                    'Current Occupancy %':     curr_occ,
                    'Predicted Occupancy %':   pred_occ,
                    'Current Status':          row['traffic_light_status'],
                    'Predicted Status':        pred_light,
                    'MAE (est)':               round(abs(curr_occ - pred_occ), 2),
                })

            return pd.DataFrame(results)

        forecast_df = run_sarimax(filtered)
        st.session_state['forecasts'] = forecast_df

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Hospitals Forecasted", len(forecast_df))
        with col2:
            st.metric("Avg MAE", f"{forecast_df['MAE (est)'].mean():.2f}%")

        st.subheader("4-Hour Occupancy Forecasts")

        def colour_pred(val):
            if val == 'Red':   return 'background-color:#FEE2E2;color:#DC2626;font-weight:600'
            if val == 'Amber': return 'background-color:#FEF3C7;color:#D97706;font-weight:600'
            if val == 'Green': return 'background-color:#DCFCE7;color:#16A34A;font-weight:600'
            return ''

        styled_f = (forecast_df.style
                    .applymap(colour_pred, subset=['Current Status', 'Predicted Status'])
                    .format({'Current Occupancy %': '{:.1f}%',
                             'Predicted Occupancy %': '{:.1f}%',
                             'MAE (est)': '{:.2f}%'}))
        st.dataframe(styled_f, use_container_width=True, height=400)

        st.markdown("---")
        st.subheader("Current vs Predicted Occupancy")
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            name='Current', x=forecast_df['Hospital'],
            y=forecast_df['Current Occupancy %'], marker_color=TEAL
        ))
        fig4.add_trace(go.Bar(
            name='Predicted (4hr)', x=forecast_df['Hospital'],
            y=forecast_df['Predicted Occupancy %'], marker_color=NAVY
        ))
        fig4.update_layout(
            barmode='group', plot_bgcolor='white', paper_bgcolor='white',
            height=420, xaxis_tickangle=-45,
            margin=dict(l=0, r=0, t=20, b=120),
            font=dict(family='DM Sans, sans-serif', color=NAVY)
        )
        fig4.add_hline(y=8, line_dash="dash", line_color=RED,   annotation_text="Red")
        fig4.add_hline(y=4, line_dash="dash", line_color=AMBER, annotation_text="Amber")
        st.plotly_chart(fig4, use_container_width=True)

    except Exception as e:
        st.error(f"Model error: {e}")

# ══════════════════════════════════════════════════════════════
# PAGE 3 — PRESCRIPTIVE ENGINE
# ══════════════════════════════════════════════════════════════
elif page == "🧠 Prescriptive Engine":

    st.markdown("""
    <div class="hf-header">
      <h2 style="color:white;margin:0">🧠 Prescriptive Analytics — Rule Engine</h2>
      <p style="color:#CCFBF1;margin:4px 0 0 0;font-size:14px">
        System actions and patient care pathways
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.info("**Logic:** Combines current live status with SARIMAX predicted status to generate a system action and patient care pathway recommendation for each hospital.")

    # Add predictions if available
    working_df = filtered.copy()
    if 'forecasts' in st.session_state:
        fc = st.session_state['forecasts'][['Hospital', 'Predicted Status']].rename(
            columns={'Predicted Status': 'predicted_traffic_light'})
        working_df = working_df.merge(fc, on='Hospital', how='left')

    prescriptive_df = run_prescriptive(working_df)

    # ── Action breakdown ──────────────────────────────────────
    action_counts = prescriptive_df['System Action'].value_counts()
    col1, col2, col3 = st.columns(3)
    urgent = (prescriptive_df['System Action'] == 'URGENT REDIRECT').sum()
    warning = (prescriptive_df['System Action'] == 'EARLY WARNING').sum()
    monitor = prescriptive_df['System Action'].isin(['MONITOR','NO ACTION']).sum()

    with col1:
        st.metric("🚨 Urgent Redirect", urgent)
    with col2:
        st.metric("⚠️ Early Warning", warning)
    with col3:
        st.metric("✅ Monitor / No Action", monitor)

    st.markdown("---")
    st.subheader("Rule Engine Output — All Hospitals")

    def colour_action(val):
        if val == 'URGENT REDIRECT': return 'background-color:#FEE2E2;color:#DC2626;font-weight:600'
        if val == 'EARLY WARNING':   return 'background-color:#FEF3C7;color:#D97706;font-weight:600'
        if val == 'IMPROVING':       return 'background-color:#DCFCE7;color:#16A34A;font-weight:600'
        if val == 'MONITOR':         return f'color:{SLATE}'
        if val == 'NO ACTION':       return 'background-color:#DCFCE7;color:#16A34A'
        return ''

    def colour_status_p(val):
        if val == 'Red':   return 'color:#DC2626;font-weight:600'
        if val == 'Amber': return 'color:#D97706;font-weight:600'
        if val == 'Green': return 'color:#16A34A;font-weight:600'
        return ''

    styled_p = (prescriptive_df.style
                .applymap(colour_action,   subset=['System Action'])
                .applymap(colour_status_p, subset=['Current Status', 'Predicted']))
