# app.py

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import altair as alt
import os

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="PM2.5 & PM10 Monitoring Dashboard", layout="wide")

# ---------------------- CUSTOM FULL BLUE THEME ----------------------
st.markdown("""
    <style>
    html, body, .main {
        background-color: #001f3f;
        color: white;
        font-family: 'Segoe UI', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #003366;
        color: white;
        border-right: 2px solid #004080;
        padding: 1rem;
    }
    h1, h2, h3, h4, .st-bb, .st-cb, label, p, div, span {
        color: #ffffff !important;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #007bff;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    .block-container {
        padding: 1rem 2rem;
    }
    .stMarkdown, .stDataFrameContainer, .stSelectbox, .stMetric {
        background-color: transparent !important;
    }
    .stDataFrameContainer .css-1y4p8pa, .stDataFrameContainer .e1tzin5v2 {
        background-color: #001f3f !important;
        color: white !important;
    }
    .css-1offfwp, .stDataFrameContainer table {
        background-color: #001f3f;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------- HEADER ----------------------
col1, col2, col3 = st.columns([1, 5, 1])
with col1:
    st.image("ISRO-Color.png", width=120)
with col2:
    st.markdown("""
        <h2 style='text-align: center;'>ISRO & CPCB AIR POLLUTION LIVE MONITORING SITE</h2>
        <h5 style='text-align: center;'>Real-Time Air Quality Monitoring</h5>
    """, unsafe_allow_html=True)
with col3:
    st.image("cpcb.png", width=120)

st.markdown("---")

# ---------------------- HELPER ----------------------
def get_pm_color(pm):
    if pm <= 60:
        return 'green'
    elif pm <= 120:
        return 'orange'
    else:
        return 'red'

# ---------------------- HIGH-RESOLUTION MAP ----------------------
st.markdown("### 🌏 High-Resolution PM2.5 Prediction Map (Folium)")

try:
    df_highres = pd.read_csv("data/high_res_input_sample_100.csv")
    df_highres.rename(columns=lambda x: x.strip(), inplace=True)

    if 'PM2.5' not in df_highres.columns:
        st.error("Column 'PM2.5' not found.")
        st.stop()

    m = folium.Map(location=[22.5, 80.0], zoom_start=5, tiles='CartoDB dark_matter')
    for _, row in df_highres.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=5,
            color=get_pm_color(row['PM2.5']),
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(f"PM2.5: {row['PM2.5']:.2f}", max_width=150)
        ).add_to(m)

    st_data = st_folium(m, width=1100, height=550)

    with st.expander("📋 Show High-Resolution Prediction Table"):
        st.dataframe(df_highres.round(2))

    st.download_button(
        label="📅 Download High-Res Predictions",
        data=df_highres.to_csv(index=False).encode(),
        file_name="high_res_predictions.csv",
        mime="text/csv"
    )

except FileNotFoundError:
    st.error("❌ File `data/high_res_input_sample_100.csv` not found.")

st.markdown("---")

# ---------------------- CITY-WISE MONITORING ----------------------
st.markdown("### 🌐 Multi-City Live PM2.5 & PM10 Monitoring Dashboard")

st.sidebar.header("🔧 Configuration")
city_files = {
    "Delhi": "data/delhi_pm_data.csv",
    "Bangalore": "data/bangalore_pm_data.csv",
    "Hyderabad": "data/hyderabad_pm_data.csv",
    "Kolkata": "data/kolkata_pm_data.csv"
}
selected_cities = st.sidebar.multiselect("Select Cities", list(city_files.keys()), default=["Delhi"])
refresh_interval = st.sidebar.selectbox("Refresh Interval (seconds)", [1, 5, 10], index=1)

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
    st.error("No valid city data found. Please check files in `data/` folder.")
    st.stop()

df_all = pd.concat(all_frames, ignore_index=True)
df_all.rename(columns=lambda x: x.strip(), inplace=True)

if 'PM2.5' not in df_all.columns or 'PM10' not in df_all.columns:
    st.error("Required columns 'PM2.5' and 'PM10' not found.")
    st.stop()

# ---------------------- DISPLAY CITY-WISE ----------------------
for city in selected_cities:
    city_df = df_all[df_all["city"] == city]
    if city_df.empty:
        continue

    latest_row = city_df.iloc[-1]
    lat, lon = latest_row["latitude"], latest_row["longitude"]

    st.markdown(f"## 🏩 {city} | ⏱️ Hour: {int(latest_row['hour'])}")
    col1, col2 = st.columns(2)
    col1.metric("PM2.5", f"{latest_row['PM2.5']:.2f} μg/m³")
    col2.metric("PM10", f"{latest_row['PM10']:.2f} μg/m³")

    m_city = folium.Map(location=[lat, lon], zoom_start=7, tiles='CartoDB dark_matter')
    for _, row in city_df.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=5,
            color=get_pm_color(row['PM2.5']),
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(f"PM2.5: {row['PM2.5']:.2f}, PM10: {row['PM10']:.2f}", max_width=150)
        ).add_to(m_city)

    st_folium(m_city, width=1100, height=450)

    chart_data = city_df.tail(10)
    melted = pd.melt(chart_data, id_vars=["hour"], value_vars=["PM2.5", "PM10"],
                     var_name="Pollutant", value_name="Concentration")

    chart = alt.Chart(melted).mark_line(point=True).encode(
        x=alt.X("hour:O", title="Hour"),
        y=alt.Y("Concentration:Q", title="μg/m³"),
        color="Pollutant:N",
        tooltip=["hour", "Pollutant", "Concentration"]
    ).properties(title=f"📊 Last 10 Readings - {city}", height=300)

    st.altair_chart(chart, use_container_width=True)
    st.markdown("---")

# ---------------------- DOWNLOAD ALL ----------------------
st.download_button(
    label="📅 Download All City Data",
    data=df_all.to_csv(index=False).encode(),
    file_name="all_city_pm_predictions.csv",
    mime="text/csv"
)
