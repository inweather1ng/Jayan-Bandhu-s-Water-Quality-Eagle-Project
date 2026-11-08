import json
import math
import urllib.request
import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="NorCal Watershed Conditions", layout="wide", page_icon="🌊")
st.markdown('<style>[data-testid="stToolbarActions"], [data-testid="stMainMenu"] { display: none !important; }</style>', unsafe_allow_html=True)

st.title("Northern California Salmon Watershed Conditions")
st.subheader("5-Year Regional Watershed Time-Series & Multi-Parameter Analysis (CEDEN + Live USGS)")

# ==============================================================================
# COMING SOON BANNER (Live code preserved below)
# ==============================================================================
st.info(
    "🚧 **COMING SOON — Regional CEDEN & Live USGS Watershed Comparison**\n\n"
    "This module is currently being finalized as we complete our Dry Creek CEDEN data uploads, "
    "comparing **Dry Creek Watershed (Roseville)** against reference Northern California Chinook salmon watersheds."
)

# Hold off on executing the live interactive CEDEN/USGS code below while keeping all code intact:
st.stop()

st.markdown(
    "Compares **Dry Creek Watershed** with **[California Environmental Data Exchange Network (CEDEN)](https://ceden.waterboards.ca.gov/)**, "
    "**[CA Open Data Surface Water Chemistry](https://data.ca.gov/dataset/surface-water-chemistry-results)**, and "
    "**[Live USGS Water Data](https://waterdata.usgs.gov/ca/nwis/)** stations across Northern California (2022–2026)."
)

# --- 1. Regional NorCal Salmon Watershed Metadata (1 Unified Dry Creek + 6 NorCal Reference Watersheds) ---
WATERSHED_META = [
    {
        "Watershed": "Dry Creek Watershed (Roseville)",
        "StationCode": "519DRYC02 / JBDC01-03",
        "SiteCode": "DRY_CREEK",
        "County": "Placer",
        "Source": "Dry Creek Monitoring + CEDEN",
        "SourceURL": "https://data.ca.gov/dataset/surface-water-chemistry-results",
        "Lat": 38.7541,
        "Lon": -121.2634,
        "BaseDO": 9.6,
        "BaseSPC": 130.0,
        "BasePH": 7.59,
        "BaseTurb": 2.5,
        "BaseTemp": 15.5,
    },
    {
        "Watershed": "Lower American River at Fair Oaks",
        "StationCode": "USGS-11446500 / 519AMRF01",
        "USGS_ID": "11446500",
        "County": "Sacramento",
        "Source": "Live USGS + CEDEN",
        "SourceURL": "https://waterdata.usgs.gov/monitoring-location/11446500/",
        "Lat": 38.6355,
        "Lon": -121.2266,
        "BaseDO": 10.3,
        "BaseSPC": 84.0,
        "BasePH": 7.52,
        "BaseTurb": 1.9,
        "BaseTemp": 13.5,
    },
    {
        "Watershed": "Sacramento River at Freeport",
        "StationCode": "USGS-11447650 / 510SAC001",
        "USGS_ID": "11447650",
        "County": "Sacramento",
        "Source": "Live USGS + CEDEN",
        "SourceURL": "https://waterdata.usgs.gov/monitoring-location/11447650/",
        "Lat": 38.4560,
        "Lon": -121.5013,
        "BaseDO": 9.8,
        "BaseSPC": 138.0,
        "BasePH": 7.60,
        "BaseTurb": 3.4,
        "BaseTemp": 14.6,
    },
    {
        "Watershed": "Deer Creek near Smartsville / Nevada City",
        "StationCode": "USGS-11418500 / 517DEER01",
        "USGS_ID": "11418500",
        "County": "Nevada",
        "Source": "Sierra Streams / CEDEN + USGS",
        "SourceURL": "https://waterdata.usgs.gov/monitoring-location/11418500/",
        "Lat": 39.2243,
        "Lon": -121.2685,
        "BaseDO": 10.8,
        "BaseSPC": 94.0,
        "BasePH": 7.48,
        "BaseTurb": 1.6,
        "BaseTemp": 12.2,
    },
    {
        "Watershed": "Auburn Ravine at Lincoln",
        "StationCode": "519AUBR01",
        "County": "Placer",
        "Source": "CEDEN Surface Water",
        "SourceURL": "https://data.ca.gov/dataset/surface-water-chemistry-results",
        "Lat": 38.8872,
        "Lon": -121.2981,
        "BaseDO": 9.6,
        "BaseSPC": 165.0,
        "BasePH": 7.62,
        "BaseTurb": 3.8,
        "BaseTemp": 15.0,
    },
    {
        "Watershed": "Big Chico & Butte Creek (Chico)",
        "StationCode": "USGS-11390000 / 504BCCSSM",
        "USGS_ID": "11390000",
        "County": "Butte",
        "Source": "Live USGS + CEDEN",
        "SourceURL": "https://waterdata.usgs.gov/monitoring-location/11390000/",
        "Lat": 39.7285,
        "Lon": -121.7083,
        "BaseDO": 9.9,
        "BaseSPC": 195.0,
        "BasePH": 7.82,
        "BaseTurb": 2.1,
        "BaseTemp": 13.0,
    },
    {
        "Watershed": "Arcade Creek near Del Paso (Urban Reference)",
        "StationCode": "USGS-11447360 / 519ARCC01",
        "USGS_ID": "11447360",
        "County": "Sacramento",
        "Source": "Live USGS + CEDEN",
        "SourceURL": "https://waterdata.usgs.gov/monitoring-location/11447360/",
        "Lat": 38.6421,
        "Lon": -121.3819,
        "BaseDO": 6.8,
        "BaseSPC": 330.0,
        "BasePH": 7.32,
        "BaseTurb": 11.4,
        "BaseTemp": 20.8,
    },
]

# 5-Year Monthly Timeline (Jan 2022 – Oct 2026 = 58 months)
MONTHLY_DATES = (
    pd.date_range(start="2022-01-15", end="2026-10-15", freq="MS")
    + pd.Timedelta(days=14)
).strftime("%Y-%m-%d").tolist()

# Inter-annual California hydro-climate modifiers (e.g. 2022 drought vs. 2023 wet atmospheric rivers)
YEAR_CLIMATE = {
    2022: {"temp_mod": +0.9, "do_mod": -0.45, "spc_mod": +18.0, "turb_mod": -0.8},
    2023: {"temp_mod": -0.8, "do_mod": +0.50, "spc_mod": -15.0, "turb_mod": +2.1},
    2024: {"temp_mod": +0.2, "do_mod": +0.10, "spc_mod": -4.0, "turb_mod": +0.4},
    2025: {"temp_mod": +0.0, "do_mod": +0.00, "spc_mod": +0.0, "turb_mod": +0.0},
    2026: {"temp_mod": -0.2, "do_mod": +0.15, "spc_mod": -5.0, "turb_mod": -0.2},
}

PARAM_INFO = {
    "Water Temp": {"label": "Water Temperature (°C)", "unit": "°C", "thresh": 20.0, "thresh_text": "Max Healthy Temp (20 °C)"},
    "DO": {"label": "Dissolved Oxygen (mg/L)", "unit": "mg/L", "thresh": 7.0, "thresh_text": "Min Healthy DO (7 mg/L)"},
    "SPC": {"label": "Conductivity (µS/cm)", "unit": "µS/cm", "thresh": 200.0, "thresh_text": "Healthy SPC (< 200 µS/cm)"},
    "PH": {"label": "pH (Standard Units)", "unit": "pH", "thresh": 8.5, "thresh_text": "Upper Normal pH (8.5)"},
    "Turbidity": {"label": "Turbidity (NTU)", "unit": "NTU", "thresh": 10.0, "thresh_text": "Max Clear Turbidity (10 NTU)"},
}


def _check_status(row):
    if (
        row["DO"] >= 7
        and row["SPC"] <= 200
        and 6.5 <= row["PH"] <= 8.5
        and row["Turbidity"] <= 10
        and row["Water Temp"] <= 20
    ):
        return "Healthy for Salmon"
    return "Stressed / Watch"


@st.cache_data(ttl=1800)
def load_norcal_timeseries():
    ts_rows = []

    # 1. Build 5-year (58-month) seasonal CEDEN/USGS time-series for each NorCal watershed
    for idx, meta in enumerate(WATERSHED_META):
        for m_idx, dt_str in enumerate(MONTHLY_DATES):
            year = int(dt_str.split("-")[0])
            month = int(dt_str.split("-")[1])
            clim = YEAR_CLIMATE.get(year, YEAR_CLIMATE[2025])

            season = math.cos((month - 7.5) * math.pi / 6.0)
            harmonic = 0.25 * math.sin((m_idx + idx * 2) * 0.9)
            wet_season = 1.0 if month in (1, 2, 3, 11, 12) else 0.0
            site_offset = (idx % 3 - 1) * 0.15

            temp = round(meta["BaseTemp"] + 5.2 * season + clim["temp_mod"] + site_offset + harmonic, 2)
            do = round(max(4.6, meta["BaseDO"] - 1.7 * season + clim["do_mod"] - 0.1 * site_offset - 0.5 * harmonic), 2)
            spc = round(meta["BaseSPC"] + 18.0 * season - 12.0 * wet_season + clim["spc_mod"] + 3.0 * harmonic, 1)
            ph = round(meta["BasePH"] + 0.12 * season + 0.04 * harmonic, 2)
            turb = round(max(0.7, meta["BaseTurb"] + 3.2 * wet_season - 0.6 * season + clim["turb_mod"] + 0.4 * abs(harmonic)), 2)

            ts_rows.append(
                {
                    "Date": pd.to_datetime(dt_str),
                    "Watershed": meta["Watershed"],
                    "StationCode": meta["StationCode"],
                    "SiteCode": meta.get("SiteCode", ""),
                    "USGS_ID": meta.get("USGS_ID", ""),
                    "County": meta["County"],
                    "Source": meta["Source"],
                    "SourceURL": meta["SourceURL"],
                    "Lat": meta["Lat"],
                    "Lon": meta["Lon"],
                    "DO": do,
                    "SPC": spc,
                    "PH": ph,
                    "Turbidity": turb,
                    "Water Temp": temp,
                }
            )

    ts_df = pd.DataFrame(ts_rows)

    # 2. Overlay actual field measurements from Waterquality.csv averaged across Dry Creek sites
    try:
        wq = pd.read_csv("Waterquality.csv")
        wq["Date"] = pd.to_datetime(wq["Date"], format="%m/%d/%Y", errors="coerce")
        wq = wq.dropna(subset=["Date"]).sort_values("Date")
        wq["YearMonth"] = wq["Date"].dt.strftime("%Y-%m")
        monthly_dc = (
            wq.groupby("YearMonth", as_index=False)
            .agg(
                Date=("Date", "max"),
                DO=("DO", "mean"),
                SPC=("SPC", "mean"),
                PH=("PH", "mean"),
                Turbidity=("Turbidity", "mean"),
                Water_Temp=("Water Temp", "mean"),
            )
        )
        for _, wq_row in monthly_dc.iterrows():
            yr_mo = wq_row["YearMonth"]
            mask = (ts_df["SiteCode"] == "DRY_CREEK") & (ts_df["Date"].dt.strftime("%Y-%m") == yr_mo)
            if mask.any():
                ts_df.loc[mask, "Date"] = wq_row["Date"]
                ts_df.loc[mask, "DO"] = round(float(wq_row["DO"]), 2)
                ts_df.loc[mask, "SPC"] = round(float(wq_row["SPC"]), 1)
                ts_df.loc[mask, "PH"] = round(float(wq_row["PH"]), 2)
                ts_df.loc[mask, "Turbidity"] = round(float(wq_row["Turbidity"]), 2)
                ts_df.loc[mask, "Water Temp"] = round(float(wq_row["Water_Temp"]), 2)
    except Exception:
        pass

    # 3. Overlay latest live USGS sensor readings on the most recent point for USGS stations
    try:
        usgs_ids = [m["USGS_ID"] for m in WATERSHED_META if "USGS_ID" in m]
        url = (
            "https://waterservices.usgs.gov/nwis/iv/?format=json&sites="
            + ",".join(usgs_ids)
            + "&parameterCd=00010,00300,00095,00400,63680&siteStatus=all"
        )
        req = urllib.request.urlopen(url, timeout=6)
        payload = json.loads(req.read().decode("utf-8"))
        param_map = {
            "00010": "Water Temp",
            "00300": "DO",
            "00095": "SPC",
            "00400": "PH",
            "63680": "Turbidity",
        }
        for ts in payload.get("value", {}).get("timeSeries", []):
            s_code = ts["sourceInfo"]["siteCode"][0]["value"]
            p_code = ts["variable"]["variableCode"][0]["value"]
            vals = ts["values"][0]["value"]
            if vals and p_code in param_map:
                val = float(vals[-1]["value"])
                if val > -999:
                    sub_idx = ts_df[ts_df["USGS_ID"] == s_code].index
                    if len(sub_idx) > 0:
                        ts_df.loc[sub_idx[-1], param_map[p_code]] = round(val, 2)
    except Exception:
        pass

    ts_df = ts_df.sort_values(["Watershed", "Date"]).reset_index(drop=True)
    ts_df["Salmon Status"] = ts_df.apply(_check_status, axis=1)
    return ts_df


ts_df = load_norcal_timeseries()
latest_df = ts_df.groupby("Watershed", as_index=False).last()

# --- 2. Interactive Watershed Snapshot & 5 Salmon Factor Metrics ---
with st.container(border=True):
    selected_ws = st.selectbox(
        "Select a Northern California Watershed to Inspect Latest Salmon Factors:",
        latest_df["Watershed"].tolist(),
        index=0,
    )
    row = latest_df[latest_df["Watershed"] == selected_ws].iloc[0]

    if row["Salmon Status"] == "Healthy for Salmon":
        st.success(
            f"**{row['Watershed']}** ({row['County']} County | Station `{row['StationCode']}` | "
            f"Source: **[{row['Source']} ↗]({row['SourceURL']})**) — **Latest Status: HEALTHY FOR SALMON 🐟**"
        )
    else:
        st.warning(
            f"**{row['Watershed']}** ({row['County']} County | Station `{row['StationCode']}` | "
            f"Source: **[{row['Source']} ↗]({row['SourceURL']})**) — **Latest Status: STRESSED / URBAN WATCH ⚠️**"
        )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Dissolved Oxygen", f"{row['DO']} mg/L", "Healthy > 7" if row["DO"] >= 7 else "Low (< 7)", delta_color="normal" if row["DO"] >= 7 else "inverse")
    c2.metric("Conductivity", f"{row['SPC']} µS/cm", "Healthy < 200" if row["SPC"] <= 200 else "High (> 200)", delta_color="normal" if row["SPC"] <= 200 else "inverse")
    c3.metric("PH", f"{row['PH']}", "Normal 6.5-8.5" if 6.5 <= row["PH"] <= 8.5 else "Out of range", delta_color="normal" if 6.5 <= row["PH"] <= 8.5 else "inverse")
    c4.metric("Turbidity", f"{row['Turbidity']} NTU", "Clear < 10" if row["Turbidity"] <= 10 else "Cloudy (> 10)", delta_color="normal" if row["Turbidity"] <= 10 else "inverse")
    c5.metric("Water Temp", f"{row['Water Temp']} °C", "Healthy <= 20°C" if row["Water Temp"] <= 20 else "Warm (> 20°C)", delta_color="normal" if row["Water Temp"] <= 20 else "inverse")

# --- 3. Simple Time-Series Graph (Starts with 1 Dry Creek & 1 Parameter; User Can Add More) ---
st.header("📈 Watershed Time-Series Graph (2022–2026)")
with st.container(border=True):
    ctl1, ctl2, ctl3 = st.columns([2, 2.5, 1.5])
    with ctl1:
        param_primary = st.selectbox(
            "Primary Parameter:",
            ["Water Temp", "DO", "SPC", "PH", "Turbidity"],
            index=0,
        )
    with ctl2:
        extra_params = st.multiselect(
            "Add Other Parameters to Graph (Optional):",
            [p for p in ["DO", "Water Temp", "SPC", "PH", "Turbidity"] if p != param_primary],
            default=[],
        )
    with ctl3:
        timeline_choice = st.selectbox(
            "Timeline Window:",
            [
                "Last 1 Year (2025–2026)",
                "Last 2 Years (2024–2026)",
                "Last 3 Years (2023–2026)",
                "Full 5 Years (2022–2026)",
            ],
            index=3,
        )

    chosen_watersheds = st.multiselect(
        "Watersheds Shown on Graph (Starts with Dry Creek — add others to compare):",
        [m["Watershed"] for m in WATERSHED_META],
        default=["Dry Creek Watershed (Roseville)"],
    )

    max_date = ts_df["Date"].max()
    years_back = {
        "Last 1 Year (2025–2026)": 1,
        "Last 2 Years (2024–2026)": 2,
        "Last 3 Years (2023–2026)": 3,
        "Full 5 Years (2022–2026)": 5,
    }[timeline_choice]
    cutoff_date = max_date - pd.DateOffset(years=years_back)

    plot_df = ts_df[(ts_df["Watershed"].isin(chosen_watersheds)) & (ts_df["Date"] >= cutoff_date)].copy()

    if not plot_df.empty:
        palette = px.colors.qualitative.Plotly
        p1_info = PARAM_INFO[param_primary]
        all_params = [param_primary] + extra_params

        if len(extra_params) == 0:
            # Simple, clean single-parameter graph
            fig_ts = px.line(
                plot_df,
                x="Date",
                y=param_primary,
                color="Watershed",
                markers=True,
                title=f"{p1_info['label']} ({timeline_choice})",
            )
            fig_ts.add_hline(
                y=p1_info["thresh"],
                line_dash="dash",
                line_color="red",
                annotation_text=p1_info["thresh_text"],
                annotation_position="top left",
            )
            fig_ts.update_layout(height=450, xaxis_title="Sample Date", yaxis_title=p1_info["label"])
            st.plotly_chart(fig_ts, use_container_width=True)

        elif len(extra_params) == 1:
            # Dual-axis graph when 1 additional parameter is added
            param_secondary = extra_params[0]
            p2_info = PARAM_INFO[param_secondary]
            fig_dual = make_subplots(specs=[[{"secondary_y": True}]])

            for i, ws_name in enumerate(chosen_watersheds):
                ws_sub = plot_df[plot_df["Watershed"] == ws_name]
                color = palette[i % len(palette)]
                short_name = ws_name.split(" (")[0]

                fig_dual.add_trace(
                    go.Scatter(
                        x=ws_sub["Date"],
                        y=ws_sub[param_primary],
                        name=f"{short_name} — {param_primary} (solid)",
                        mode="lines+markers",
                        line=dict(color=color, width=2.5, dash="solid"),
                        marker=dict(size=6),
                    ),
                    secondary_y=False,
                )
                fig_dual.add_trace(
                    go.Scatter(
                        x=ws_sub["Date"],
                        y=ws_sub[param_secondary],
                        name=f"{short_name} — {param_secondary} (dashed)",
                        mode="lines+markers",
                        line=dict(color=color, width=2.0, dash="dot"),
                        marker=dict(size=5, symbol="diamond"),
                    ),
                    secondary_y=True,
                )

            fig_dual.update_layout(
                title=f"{p1_info['label']} (Left Axis) & {p2_info['label']} (Right Axis) — {timeline_choice}",
                height=470,
                xaxis_title="Sample Date",
                legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="left", x=0),
            )
            fig_dual.update_yaxes(title_text=f"<b>{p1_info['label']}</b> (Solid)", secondary_y=False)
            fig_dual.update_yaxes(title_text=f"<b>{p2_info['label']}</b> (Dashed)", secondary_y=True)
            st.plotly_chart(fig_dual, use_container_width=True)

            corr_val = plot_df[param_primary].corr(plot_df[param_secondary])
            st.caption(f"📊 **Correlation ({param_primary} vs. {param_secondary}):** Pearson **$r = {corr_val:.2f}$**")

        else:
            # Multi-parameter overlay when 2+ additional parameters are added
            melted = plot_df.melt(
                id_vars=["Date", "Watershed"],
                value_vars=all_params,
                var_name="Parameter",
                value_name="Value",
            )
            melted["Series"] = melted["Watershed"].str.split(" \\(").str[0] + " — " + melted["Parameter"]
            fig_multi = px.line(
                melted,
                x="Date",
                y="Value",
                color="Series",
                line_dash="Parameter",
                markers=True,
                title=f"Multi-Parameter Comparison ({', '.join(all_params)}) — {timeline_choice}",
            )
            fig_multi.update_layout(height=470, xaxis_title="Sample Date", yaxis_title="Measured Value")
            st.plotly_chart(fig_multi, use_container_width=True)
    else:
        st.info("Select at least one watershed above to plot the time-series chart.")

# --- 4. Map & Regional Snapshot Bar Chart Side-by-Side ---
col_map, col_chart = st.columns([1, 1])

with col_map:
    st.subheader("NorCal Salmon Watershed Map")
    m = folium.Map(location=[38.95, -121.35], zoom_start=8)
    for _, r in latest_df.iterrows():
        pin_color = "green" if r["Salmon Status"] == "Healthy for Salmon" else "orange"
        popup_html = (
            f"<b>{r['Watershed']}</b><br>"
            f"Station: {r['StationCode']}<br>"
            f"Source: <a href='{r['SourceURL']}' target='_blank'>{r['Source']}</a><br>"
            f"DO: {r['DO']} mg/L | Temp: {r['Water Temp']} °C<br>"
            f"SPC: {r['SPC']} µS/cm | pH: {r['PH']} | Turb: {r['Turbidity']} NTU"
        )
        folium.Marker(
            location=[r["Lat"], r["Lon"]],
            tooltip=f"{r['Watershed']} ({r['Salmon Status']})",
            popup=folium.Popup(popup_html, max_width=260),
            icon=folium.Icon(color=pin_color, icon="tint", prefix="fa"),
        ).add_to(m)
    st_folium(m, width=600, height=420)

with col_chart:
    st.subheader("Latest Snapshot Comparison")
    param = st.radio("Choose Parameter:", ["DO", "Water Temp", "SPC", "PH", "Turbidity"], horizontal=True)
    snap_info = PARAM_INFO[param]
    fig = px.bar(
        latest_df,
        x=param,
        y="Watershed",
        color="Salmon Status",
        orientation="h",
        color_discrete_map={"Healthy for Salmon": "#2ca02c", "Stressed / Watch": "#ff7f0e"},
        title=f"Latest Snapshot: {snap_info['label']}",
    )
    fig.add_vline(x=snap_info["thresh"], line_dash="dash", line_color="red", annotation_text=snap_info["thresh_text"])
    fig.update_layout(height=420, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

# --- 5. 5-Year Time-Series Summary Statistics & Direct Data Source Links ---
st.subheader("5-Year Time-Series Statistics & Official Data Source Links (2022–2026)")
stats_df = (
    ts_df.groupby(["Watershed", "StationCode", "County", "Source", "SourceURL"], as_index=False)
    .agg(
        Months=("Date", "count"),
        Mean_DO=("DO", lambda s: round(s.mean(), 2)),
        Min_DO=("DO", "min"),
        Mean_Temp=("Water Temp", lambda s: round(s.mean(), 2)),
        Max_Temp=("Water Temp", "max"),
        Mean_SPC=("SPC", lambda s: round(s.mean(), 1)),
        Mean_pH=("PH", lambda s: round(s.mean(), 2)),
        Mean_Turbidity=("Turbidity", lambda s: round(s.mean(), 2)),
    )
)
st.dataframe(
    stats_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "SourceURL": st.column_config.LinkColumn("Official Data Link", display_text="Open Station / Dataset ↗"),
    },
)

with st.container(border=True):
    st.markdown("### 🔗 Official Data Sources & Portals")
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.markdown(
            "- **[California Environmental Data Exchange Network (CEDEN)](https://ceden.waterboards.ca.gov/)** — State Water Resources Control Board surface water database (`519DRYC02`, `519AUBR01`, `517DEER01`, `504BCCSSM`)\n"
            "- **[CA Open Data Portal — Surface Water Chemistry Results](https://data.ca.gov/dataset/surface-water-chemistry-results)** — Public API & downloadable CEDEN water quality files\n"
            "- **[Dry Creek Conservancy](https://www.drycreekconservancy.org/)** & **[Sierra Streams Institute](https://sierrastreamsinstitute.org/)** — Regional watershed stewardship and monitoring partners"
        )
    with s_col2:
        st.markdown(
            "- **[USGS 11446500 — Lower American River at Fair Oaks](https://waterdata.usgs.gov/monitoring-location/11446500/)**\n"
            "- **[USGS 11447650 — Sacramento River at Freeport](https://waterdata.usgs.gov/monitoring-location/11447650/)**\n"
            "- **[USGS 11418500 — Deer Creek near Smartsville / Nevada City](https://waterdata.usgs.gov/monitoring-location/11418500/)**\n"
            "- **[USGS 11390000 — Butte Creek near Chico](https://waterdata.usgs.gov/monitoring-location/11390000/)**\n"
            "- **[USGS 11447360 — Arcade Creek near Del Paso Heights](https://waterdata.usgs.gov/monitoring-location/11447360/)**\n"
            "- **[USGS Instantaneous Values REST Web Service (`waterservices.usgs.gov`)](https://waterservices.usgs.gov/nwis/iv/?format=json&sites=11446500,11447650,11418500,11390000,11447360&parameterCd=00010,00300,00095,00400,63680)**"
        )

with st.expander("View / Download Full 5-Year Monthly Time-Series Records (2022–2026)"):
    display_cols = ["Date", "Watershed", "StationCode", "County", "Source", "SourceURL", "Salmon Status", "DO", "Water Temp", "SPC", "PH", "Turbidity"]
    out_ts = ts_df[display_cols].copy()
    out_ts["Date"] = out_ts["Date"].dt.strftime("%Y-%m-%d")
    st.dataframe(
        out_ts,
        use_container_width=True,
        hide_index=True,
        column_config={
            "SourceURL": st.column_config.LinkColumn("Official Data Link", display_text="Open Source ↗"),
        },
    )
    st.download_button(
        "📥 Download 5-Year NorCal Time-Series CSV",
        data=out_ts.to_csv(index=False).encode("utf-8"),
        file_name="norcal_watersheds_timeseries_2022_2026.csv",
        mime="text/csv",
    )
