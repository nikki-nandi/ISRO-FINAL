import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import altair as alt
import time
import os

# --- CONFIG ---
st.set_page_config(page_title="PM2.5 & PM10 Monitoring Dashboard", layout="wide")

# --- CUSTOM CSS FOR DARK UI ---
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

# --- HEADER ---
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

# --- FUNCTIONS ---
def get_pm_color(pm):
    if pm <= 60:
        return [0, 200, 0]
    elif pm <= 120:
        return [255, 165, 0]
    else:
        return [255, 0, 0]

# --- HIGH-RESOLUTION MAP ---
st.markdown("### 🌏 High-Resolution PM2.5 Prediction Map")
df_highres = pd.read_csv("data/high_res_pm25_predictions.csv")
df_highres["color"] = df_highres["PM2.5_Pred"].apply(get_pm_color)

layer_map = pdk.Layer(
    "ScatterplotLayer",
    data=df_highres,
    get_position='[longitude, latitude]',
    get_radius=12000,
    get_fill_color="color",
    pickable=True,
    opacity=0.8,
)

view_map = pdk.ViewState(latitude=22.5, longitude=80.0, zoom=5.5, pitch=40)

st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/dark-v10",
    initial_view_state=view_map,
    layers=[layer_map],
    tooltip={"text": "Lat: {latitude}\nLon: {longitude}\nPM2.5: {PM2.5_Pred}"}
))

with st.expander("📋 Show High-Resolution Prediction Table"):
    st.dataframe(df_highres.round(2))

st.download_button(
    label="📅 Download High-Res Predictions",
    data=df_highres.to_csv(index=False).encode(),
    file_name="pm25_high_res_predictions.csv",
    mime="text/csv"
)

st.markdown("---")

# --- CITY-WISE LIVE DASHBOARD ---
st.markdown("### 🌐 Multi-City Live PM2.5 & PM10 Monitoring Dashboard")

city_files = {
    "Delhi": "data/delhi_pm_data.csv",
    "Bangalore": "data/bangalore_pm_data.csv",
    "Hyderabad": "data/hyderabad_pm_data.csv",
    "Kolkata": "data/kolkata_pm_data.csv"
}

st.sidebar.header("🔧 Configuration")
selected_cities = st.sidebar.multiselect("Select cities to monitor:", list(city_files.keys()), default=list(city_files.keys()))
refresh_interval = st.sidebar.selectbox("Refresh Interval (seconds)", [1, 5, 10], index=1)

frames = []
for city in selected_cities:
    path = city_files[city]
    if os.path.exists(path):
        df = pd.read_csv(path)
        df["city"] = city
        frames.append(df)
    else:
        st.warning(f"Data for {city} not found at {path}")

if not frames:
    st.stop()

# --- PROCESS ALL CITY DATA ---
df_all = pd.concat(frames, ignore_index=True)

placeholder = st.empty()
for i in range(len(df_all)):
    row = df_all.iloc[i]
    city = row["city"]

    with placeholder.container():
        st.markdown(f"### 🏠 {city} | ⏱️ Hour: {int(row['hour'])}")
        st.caption(f"🔄 Auto-refreshing every {refresh_interval} seconds")

        col1, col2 = st.columns(2)
        col1.markdown(f"""
            <div style='padding:20px;background:#112233;color:white;border-radius:10px;'>
            PM2.5<br><span style='font-size:36px'>{row['PM2.5_Pred']:.2f}</span></div>
        """, unsafe_allow_html=True)

        col2.markdown(f"""
            <div style='padding:20px;background:#112233;color:white;border-radius:10px;'>
            PM10<br><span style='font-size:36px'>{row['PM10_Pred']:.2f}</span></div>
        """, unsafe_allow_html=True)

        city_df = df_all[df_all["city"] == city].copy()
        city_df["color"] = city_df["PM2.5_Pred"].apply(get_pm_color)

        map_layer = pdk.Layer(
            "ScatterplotLayer",
            data=city_df,
            get_position='[longitude, latitude]',
            get_radius=10000,
            get_fill_color="color",
            pickable=True,
            opacity=0.8,
        )

        view = pdk.ViewState(latitude=row["latitude"], longitude=row["longitude"], zoom=5.5, pitch=30)

        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/dark-v10",
            initial_view_state=view,
            layers=[map_layer],
            tooltip={"text": "Lat: {latitude}\nLon: {longitude}\nPM2.5: {PM2.5_Pred}\nPM10: {PM10_Pred}"}
        ))

        last_10 = city_df.tail(10)
        melted = pd.melt(last_10, id_vars=["hour"], value_vars=["PM2.5_Pred", "PM10_Pred"],
                         var_name="Pollutant", value_name="Concentration")

        chart = alt.Chart(melted).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X("hour:O", title="Hour"),
            y=alt.Y("Concentration:Q", title="μg/m³"),
            color=alt.Color("Pollutant:N"),
            tooltip=["hour", "Pollutant", "Concentration"]
        ).properties(title="📊 Last 10 Readings", height=300, width=800)

        st.altair_chart(chart, use_container_width=True)
        st.markdown("---")

    time.sleep(refresh_interval)

# --- DOWNLOAD ALL ---
st.download_button(
    label="📆 Download All City Predictions",
    data=df_all.to_csv(index=False).encode(),
    file_name="all_city_pm_predictions.csv",
    mime="text/csv"
)
