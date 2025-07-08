import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import time
import altair as alt
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Air Quality Dashboard", layout="wide")

# --- DARK THEME CSS ---
st.markdown("""
    <style>
    .main { background-color: #0b1725; color: #ffffff; }
    section[data-testid="stSidebar"] {
        background-color: #08121d;
        color: white;
        border-right: 1px solid #222;
    }
    h1, h2, h3, h4 { color: #ffffff !important; }
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
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
col1, col2, col3 = st.columns([1, 5, 1])
with col1:
    st.image("ISRO-Color.png", width=150)
with col2:
    st.markdown("""
        <h2 style='text-align: center; color: #64b5f6;'>ISRO & CPCB AIR POLLUTION LIVE MONITORING SITE</h2>
        <h5 style='text-align: center; color: #a5b4c3;'>Real-Time Air Quality Monitoring (Static Data)</h5>
    """, unsafe_allow_html=True)
with col3:
    st.image("cpcb.png", width=150)

st.markdown("---")

# --- UTILS ---
def get_pm_color(pm):
    if pm <= 60:
        return [0, 200, 0]
    elif pm <= 120:
        return [255, 165, 0]
    else:
        return [255, 0, 0]

# --- SECTION 1: HIGH RES MAP (Static Display) ---
st.markdown("### 🌏 High-Resolution PM2.5 Map (Static Display)")
df_map = pd.read_csv("data/high_res_pm25_predictions.csv")
df_map["color"] = df_map["PM2.5_Pred"].apply(get_pm_color)

layer_map = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position='[longitude, latitude]',
    get_radius=10000,
    get_fill_color="color",
    pickable=True,
    opacity=0.8
)

view_map = pdk.ViewState(latitude=22.5, longitude=80.0, zoom=4.5, pitch=40)

st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/dark-v10",
    initial_view_state=view_map,
    layers=[layer_map],
    tooltip={"text": "Lat: {latitude}\nLon: {longitude}\nPM2.5: {PM2.5_Pred}"}
))

with st.expander("📋 Show High-Resolution Table"):
    st.dataframe(df_map.round(2))

st.download_button(
    label="📆 Download High-Res Data",
    data=df_map.to_csv(index=False).encode(),
    file_name="pm25_high_res_static.csv",
    mime="text/csv"
)

# --- SECTION 2: CITY MONITORING ---
st.markdown("### 🌐 Static City-Wise PM2.5 & PM10 Dashboard")

available_cities = {
    "Delhi": "data/delhi_pm_data.csv",
    "Bangalore": "data/bangalore_pm_data.csv",
    "Hyderabad": "data/hyderabad_pm_data.csv",
    "Kolkata": "data/kolkata_pm_data.csv"
}

st.sidebar.header("🔧 Configuration")
selected_cities = st.sidebar.multiselect("Select cities to display:", list(available_cities.keys()), default=list(available_cities.keys()))

frames = []
for city in selected_cities:
    path = available_cities.get(city)
    if path and os.path.exists(path):
        df = pd.read_csv(path)
        df["city"] = city
        frames.append(df)
    else:
        st.warning(f"Data for {city} not found at {path}")

if not frames:
    st.stop()

df_all = pd.concat(frames, ignore_index=True)

# Display city-level dashboard
for city in selected_cities:
    city_df = df_all[df_all["city"] == city].tail(10)
    st.markdown(f"### 🏠 {city} | Last 10 Hourly Readings")

    col1, col2 = st.columns(2)
    latest = city_df.iloc[-1]
    col1.metric("PM2.5", f"{latest['PM2.5_Pred']:.2f} µg/m³")
    col2.metric("PM10", f"{latest['PM10_Pred']:.2f} µg/m³")

    melted = pd.melt(city_df, id_vars=["hour"], value_vars=["PM2.5_Pred", "PM10_Pred"], var_name="Pollutant", value_name="Concentration")

    chart = alt.Chart(melted).mark_line(point=True).encode(
        x=alt.X("hour:O", title="Hour"),
        y=alt.Y("Concentration:Q", title="µg/m³"),
        color="Pollutant:N",
        tooltip=["hour", "Pollutant", "Concentration"]
    ).properties(title=f"{city} - PM Trends", height=350, width=850)

    st.altair_chart(chart, use_container_width=True)
    st.markdown("---")

# Final download
st.download_button(
    label="📆 Download All City Data",
    data=df_all.to_csv(index=False).encode(),
    file_name="all_city_pm_static.csv",
    mime="text/csv"
)
