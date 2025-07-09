import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import altair as alt
import os

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="PM2.5 & PM10 Monitoring Dashboard", layout="wide")

# ---------------------- CUSTOM DARK THEME ----------------------
st.markdown("""
    <style>
    .main { background-color: #0b1725; color: #ffffff; }
    section[data-testid="stSidebar"] {
        background-color: #08121d;
        color: white;
        border-right: 1px solid #222;
    }
    h1, h2, h3, h4, .st-bb, .st-cb { color: #ffffff !important; }
    .stButton>button, .stDownloadButton>button {
        background-color: #1464b4;
        color: white;
        font-weight: bold;
        border-radius: 8px;
    }
    section[data-testid="stSidebar"] label {
        color: white !important;
        font-weight: bold;
    }
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
        color: black !important;
        background-color: white !important;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------- HEADER ----------------------
col1, col2, col3 = st.columns([1, 5, 1])
with col1:
    st.image("ISRO-Color.png", width=120)
with col2:
    st.markdown("""
        <h2 style='text-align: center; color: #64b5f6;'>ISRO & CPCB AIR POLLUTION LIVE MONITORING SITE</h2>
        <h5 style='text-align: center; color: #a5b4c3;'>Real-Time Air Quality Monitoring</h5>
    """, unsafe_allow_html=True)
with col3:
    st.image("cpcb.png", width=120)

st.markdown("---")

# ---------------------- HELPER: COLOR BASED ON PM2.5 ----------------------
def get_pm_color(pm):
    if pm <= 60:
        return [0, 200, 0]          # Green
    elif pm <= 120:
        return [255, 165, 0]        # Orange
    else:
        return [255, 0, 0]          # Red

# ---------------------- HIGH RESOLUTION MAP ----------------------
st.markdown("### 🌏 High-Resolution PM2.5 Prediction Map")

df_highres = pd.read_csv("data/high_res_pm25_predictions.csv")
df_highres["color"] = df_highres["PM2.5_Pred"].apply(get_pm_color)

highres_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_highres,
    get_position='[longitude, latitude]',
    get_radius=12000,
    get_fill_color="color",
    pickable=True,
    opacity=0.8,
)

highres_view = pdk.ViewState(latitude=22.5, longitude=80.0, zoom=4.2, pitch=30)

st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/dark-v10",
    initial_view_state=highres_view,
    layers=[highres_layer],
    tooltip={"text": "Lat: {latitude}\nLon: {longitude}\nPM2.5: {PM2.5_Pred}"}
))

with st.expander("📋 Show High-Resolution Prediction Table"):
    st.dataframe(df_highres.round(2), use_container_width=True)

st.download_button(
    label="📥 Download High-Res Predictions",
    data=df_highres.to_csv(index=False).encode(),
    file_name="high_res_pm25_predictions.csv",
    mime="text/csv"
)

st.markdown("---")

# ---------------------- CITY-WISE MONITORING ----------------------
st.markdown("### 🌐 Multi-City Live PM2.5 & PM10 Monitoring Dashboard")

# Sidebar controls
st.sidebar.header("🔧 Configuration")
city_files = {
    "Delhi": "data/delhi_pm_data.csv",
    "Bangalore": "data/bangalore_pm_data.csv",
    "Hyderabad": "data/hyderabad_pm_data.csv",
    "Kolkata": "data/kolkata_pm_data.csv"
}
selected_cities = st.sidebar.multiselect("Select Cities", list(city_files.keys()), default=["Delhi"])
refresh_interval = st.sidebar.selectbox("Refresh Interval (seconds)", [1, 5, 10], index=1)

# Read all selected city data
all_frames = []
for city in selected_cities:
    file_path = city_files[city]
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df["city"] = city
        all_frames.append(df)
    else:
        st.warning(f"❌ Missing file: {file_path}")

if not all_frames:
    st.error("No valid city data found. Please check CSV files.")
    st.stop()

df_all = pd.concat(all_frames, ignore_index=True)
df_all["color"] = df_all["PM2.5_Pred"].apply(get_pm_color)

# ---------------------- DISPLAY CITY-WISE DATA ----------------------
for city in selected_cities:
    city_df = df_all[df_all["city"] == city]
    if city_df.empty:
        continue

    latest_row = city_df.iloc[-1]
    lat, lon = latest_row["latitude"], latest_row["longitude"]

    st.markdown(f"## 🏙️ {city} | ⏱️ Hour: {int(latest_row['hour'])}")
    col1, col2 = st.columns(2)
    col1.metric("PM2.5", f"{latest_row['PM2.5_Pred']:.2f} μg/m³")
    col2.metric("PM10", f"{latest_row['PM10_Pred']:.2f} μg/m³")

    city_layer = pdk.Layer(
        "ScatterplotLayer",
        data=city_df,
        get_position='[longitude, latitude]',
        get_radius=10000,
        get_fill_color="color",
        pickable=True,
        opacity=0.9
    )

    city_view = pdk.ViewState(latitude=lat, longitude=lon, zoom=6, pitch=30)

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v10",
        initial_view_state=city_view,
        layers=[city_layer],
        tooltip={"text": "Lat: {latitude}\nLon: {longitude}\nPM2.5: {PM2.5_Pred}\nPM10: {PM10_Pred}"}
    ))

    # Line chart for last 10 readings
    chart_data = city_df.tail(10)
    melted = pd.melt(chart_data, id_vars=["hour"], value_vars=["PM2.5_Pred", "PM10_Pred"],
                     var_name="Pollutant", value_name="Concentration")

    chart = alt.Chart(melted).mark_line(point=True).encode(
        x=alt.X("hour:O", title="Hour"),
        y=alt.Y("Concentration:Q", title="μg/m³"),
        color="Pollutant:N",
        tooltip=["hour", "Pollutant", "Concentration"]
    ).properties(title=f"📊 Last 10 Readings - {city}", height=300)

    st.altair_chart(chart, use_container_width=True)
    st.markdown("---")

# ---------------------- FINAL DOWNLOAD ----------------------
st.download_button(
    label="📥 Download All City Data",
    data=df_all.to_csv(index=False).encode(),
    file_name="all_city_pm_predictions.csv",
    mime="text/csv"
)
