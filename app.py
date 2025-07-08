import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import os

# ------------------- CONFIG -------------------
st.set_page_config(page_title="PM2.5 & PM10 Monitoring Dashboard", layout="wide")

# ------------------- CUSTOM CSS -------------------
st.markdown("""
    <style>
    body, .main {
        background-color: #0b1e2d !important;
        color: #ffffff !important;
        font-family: 'Segoe UI', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #081520 !important;
        color: white !important;
        border-right: 1px solid #1a2a3b;
    }
    h1, h2, h3, h4, .st-bb, .st-cb {
        color: #ffffff !important;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #2196F3;
        color: white;
        border-radius: 8px;
        padding: 0.5em 1.5em;
        font-weight: bold;
    }
    .stSelectbox>div[data-baseweb="select"], .stMultiSelect>div {
        background-color: white;
        border-radius: 10px;
        color: black;
    }
    .metric-container {
        background-color: #102738;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.3);
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------- LOAD DATA -------------------
data_dir = "data"

city_files = {
    "Delhi": os.path.join(data_dir, "delhi_pm_data.csv"),
    "Bangalore": os.path.join(data_dir, "bangalore_pm_data.csv"),
    "Hyderabad": os.path.join(data_dir, "hyderabad_pm_data.csv"),
    "Kolkata": os.path.join(data_dir, "kolkata_pm_data.csv")
}

high_res_file = os.path.join(data_dir, "high_res_pm25_predictions.csv")

df_highres = pd.read_csv(high_res_file)

# ------------------- SIDEBAR CONFIG -------------------
st.sidebar.header("🛠️ Configuration")
cities = st.sidebar.multiselect("Select cities to monitor:", list(city_files.keys()), default=["Delhi"])
interval = st.sidebar.selectbox("Refresh Interval (seconds)", [5, 10, 30, 60], index=0)

# ------------------- HEADER -------------------
st.image("ISRO-Color.png", width=120)
st.title("ISRO & CPCB AIR POLLUTION LIVE MONITORING SITE")
st.markdown("""<small>Real-Time Air Quality Monitoring</small>""", unsafe_allow_html=True)

# ------------------- HIGH RESOLUTION MAP -------------------
st.subheader("🛰️ High-Resolution PM2.5 Prediction Map")

layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_highres,
    get_position='[Longitude, Latitude]',
    get_color="[255, 255 - PM25*2, 0]",
    get_radius=25000,
    pickable=True,
    auto_highlight=True
)

view_state = pdk.ViewState(
    latitude=df_highres.Latitude.mean(),
    longitude=df_highres.Longitude.mean(),
    zoom=4.5,
    pitch=0
)

st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/dark-v10',
    layers=[layer],
    initial_view_state=view_state
))

st.download_button("📘 Download High-Res Predictions", df_highres.to_csv(index=False), "high_res_predictions.csv")

# ------------------- CITY-WISE AQ MONITORING -------------------
st.subheader("🌐 Multi-City Live PM2.5 & PM10 Monitoring Dashboard")

for city in cities:
    st.markdown(f"### 🏙️ {city}")
    df = pd.read_csv(city_files[city])
    df = df.sort_values("Hour")

    latest = df.iloc[-1]
    col1, col2 = st.columns(2)
    with col1:
        st.metric("PM2.5", f"{latest['PM2.5']:.2f}")
    with col2:
        st.metric("PM10", f"{latest['PM10']:.2f}")

    layer_city = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[Longitude, Latitude]',
        get_color="[255, 255 - PM2.5*2, 0]",
        get_radius=8000,
        pickable=True,
        auto_highlight=True
    )

    view_state_city = pdk.ViewState(
        latitude=df.Latitude.mean(),
        longitude=df.Longitude.mean(),
        zoom=6,
        pitch=0
    )

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/dark-v10',
        layers=[layer_city],
        initial_view_state=view_state_city
    ))

    st.line_chart(df.set_index("Hour")[['PM2.5', 'PM10']])

st.success(f"✅ Auto refreshing every {interval} seconds")
