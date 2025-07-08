import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Lightweight Air Pollution Dashboard", layout="wide")

# --- DARK MODE CSS ---
st.markdown("""
    <style>
    .main { background-color: #0b1725; color: #ffffff; }
    section[data-testid="stSidebar"] {
        background-color: #08121d;
        color: white;
    }
    h1, h2, h3, h4 { color: #ffffff !important; }
    .stButton>button, .stDownloadButton>button {
        background-color: #1464b4;
        color: white;
        font-weight: bold;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
col1, col2, col3 = st.columns([1, 5, 1])
with col1:
    st.image("ISRO-Color.png", width=150)
with col2:
    st.markdown("<h2 style='text-align: center; color: #64b5f6;'>ISRO & CPCB AIR POLLUTION MONITORING</h2>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align: center; color: #a5b4c3;'>Precomputed Predictions View</h5>", unsafe_allow_html=True)
with col3:
    st.image("cpcb.png", width=150)
st.markdown("---")

# --- SECTION 1: High Resolution Map (Precomputed) ---
st.markdown("### 🌏 High-Resolution PM2.5 Prediction Map")
high_res_path = "data/high_res_pm25_predictions.csv"

@st.cache_data
def load_high_res_data():
    return pd.read_csv(high_res_path)

def get_pm_color(pm):
    if pm <= 60:
        return [0, 200, 0]
    elif pm <= 120:
        return [255, 165, 0]
    else:
        return [255, 0, 0]

df_map = load_high_res_data()
df_map["color"] = df_map["PM2.5_Predicted"].apply(get_pm_color)

layer = pdk.Layer("ScatterplotLayer",
    data=df_map,
    get_position='[longitude, latitude]',
    get_radius=10000,
    get_fill_color="color",
    pickable=True,
    opacity=0.8,
)

view_state = pdk.ViewState(latitude=22.5, longitude=80.0, zoom=4.5, pitch=40)

st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/dark-v10",
    initial_view_state=view_state,
    layers=[layer],
    tooltip={"text": "Lat: {latitude}\nLon: {longitude}\nPM2.5: {PM2.5_Predicted:.2f}"}
))

with st.expander("📋 Show High-Resolution Prediction Table"):
    st.dataframe(df_map[["latitude", "longitude", "PM2.5_Predicted"]].round(2))

# --- SECTION 2: Multi-City Precomputed View ---
st.markdown("### 🌐 Multi-City PM2.5 & PM10 Monitoring")
st.sidebar.header("🔧 Configuration")

available_cities = {
    "Delhi": "data/delhi_pm_data.csv",
    "Bangalore": "data/bangalore_pm_data.csv",
    "Hyderabad": "data/hyderabad_pm_data.csv",
    "Kolkata": "data/kolkata_pm_data.csv"
}

selected_cities = st.sidebar.multiselect("Select cities:", list(available_cities.keys()), default=list(available_cities.keys()))

frames = []
for city in selected_cities:
    path = available_cities.get(city)
    if path and os.path.exists(path):
        df = pd.read_csv(path).tail(10)
        df["city"] = city
        frames.append(df)

if not frames:
    st.warning("No data found for selected cities.")
    st.stop()

df_all = pd.concat(frames, ignore_index=True)

# --- Display City-wise Charts ---
st.subheader("📊 Last 10 Readings for Selected Cities")
melted = pd.melt(df_all, id_vars=["hour", "city"], value_vars=["PM2.5_Predicted", "PM10_Predicted"], var_name="Pollutant", value_name="Concentration")

chart = alt.Chart(melted).mark_line(point=True).encode(
    x=alt.X("hour:O", title="Hour"),
    y=alt.Y("Concentration:Q", title="μg/m³"),
    color="Pollutant:N",
    tooltip=["city", "Pollutant", "Concentration", "hour"]
).properties(width=900, height=400)

st.altair_chart(chart, use_container_width=True)

# --- Table and Download ---
with st.expander("📋 Show City-Level Prediction Table"):
    st.dataframe(df_all[["city", "hour", "PM2.5_Predicted", "PM10_Predicted"]].round(2))

st.download_button(
    "📥 Download All City Data",
    data=df_all.to_csv(index=False).encode(),
    file_name="city_pm_predictions.csv",
    mime="text/csv"
)
