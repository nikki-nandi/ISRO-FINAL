# app.py

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import altair as alt
import os

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="Air Quality Dashboard", layout="wide")

# ------------------ CUSTOM UI STYLING ------------------
st.markdown("""
    <style>
    html, body, .main {
        background-color: #001F3F;
        color: white;
        font-family: 'Segoe UI', sans-serif;
    }
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    h1, h2, h3, h4, h5, h6, label, p, div, span {
        color: #ffffff !important;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #007bff;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        padding: 0.4rem 1.2rem;
        border: none;
    }
    .block-container {
        padding: 1rem 2rem 0rem 2rem;
    }
    .stDataFrameContainer table {
        background-color: #001F3F;
        color: white;
    }
    .element-container {
        padding-bottom: 0rem !important;
        margin-bottom: 0rem !important;
    }
    .stSelectbox, .stMultiSelect, .stNumberInput {
        background-color: #000000 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
col1, col2, col3 = st.columns([1, 5, 1])
with col1:
    st.image("ISRO-Color.png", width=100)
with col2:
    st.markdown("""
        <h2 style='text-align: center; color:#00bfff;'>ISRO & CPCB AIR QUALITY MONITORING</h2>
        <h5 style='text-align: center;'>Real-Time PM2.5 & PM10 Dashboard</h5>
    """, unsafe_allow_html=True)
with col3:
    st.image("cpcb.png", width=100)

st.markdown("---")

# ------------------ HELPER FUNCTION ------------------
def get_pm_color(pm):
    if pm <= 60:
        return 'green'
    elif pm <= 120:
        return 'orange'
    else:
        return 'red'

# ------------------ INPUT OPTIONS ------------------
col_conf1, col_conf2 = st.columns([3, 1])
with col_conf1:
    st.markdown("### 🌐 Select Cities")
    city_files = {
        "Delhi": "data/delhi_pm_data.csv",
        "Bangalore": "data/bangalore_pm_data.csv",
        "Hyderabad": "data/hyderabad_pm_data.csv",
        "Kolkata": "data/kolkata_pm_data.csv"
    }
    selected_cities = st.multiselect("Cities", list(city_files.keys()), default=["Delhi"])
with col_conf2:
    st.markdown("### ⏱️ Refresh Interval (sec)")
    refresh_interval = st.number_input("Interval", min_value=1, max_value=60, value=5, step=1)

st.markdown("---")

# ------------------ HIGH-RES MAP ------------------
st.markdown("### 🌏 High-Resolution PM2.5 Prediction Map")

try:
    df_highres = pd.read_csv("data/high_res_input_sample_100.csv")
    df_highres.rename(columns=lambda x: x.strip(), inplace=True)

    if 'PM2.5' not in df_highres.columns:
        st.error("Column 'PM2.5' not found in dataset.")
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

    st_folium(m, width=1300, height=550)

    with st.expander("📋 Show Prediction Data Table"):
        st.dataframe(df_highres.round(2), use_container_width=True)

    st.download_button(
        label="🗓️ Download High-Res Predictions",
        data=df_highres.to_csv(index=False).encode(),
        file_name="high_res_predictions.csv",
        mime="text/csv"
    )

except FileNotFoundError:
    st.error("❌ Missing file: data/high_res_input_sample_100.csv")

# ------------------ CITY-WISE MAP ------------------
st.markdown("### 🏙️ City-Wise PM2.5 & PM10 Monitoring")

all_frames = []
for city in selected_cities:
    file_path = city_files.get(city)
    if file_path and os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df["city"] = city
        all_frames.append(df)
    else:
        st.warning(f"❌ File not found: {file_path}")

if not all_frames:
    st.error("No city data available.")
    st.stop()

df_all = pd.concat(all_frames, ignore_index=True)
df_all.rename(columns=lambda x: x.strip(), inplace=True)

if 'PM2.5' not in df_all.columns or 'PM10' not in df_all.columns:
    st.error("Missing 'PM2.5' or 'PM10' columns.")
    st.stop()

for city in selected_cities:
    city_df = df_all[df_all["city"] == city]
    if city_df.empty:
        continue

    latest_row = city_df.iloc[-1]
    lat, lon = latest_row["latitude"], latest_row["longitude"]

    st.markdown(f"## 🏩 {city} | ⏱️ Hour: {int(latest_row['hour'])}")
    col1, col2 = st.columns(2)
    col1.metric("PM2.5 (μg/m³)", f"{latest_row['PM2.5']:.2f}")
    col2.metric("PM10 (μg/m³)", f"{latest_row['PM10']:.2f}")

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

    st_folium(m_city, width=1300, height=450)

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

# ------------------ DOWNLOAD ALL ------------------
st.download_button(
    label="📇 Download All City Data",
    data=df_all.to_csv(index=False).encode(),
    file_name="all_city_pm_predictions.csv",
    mime="text/csv"
)
