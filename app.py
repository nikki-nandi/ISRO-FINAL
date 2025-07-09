# app.py

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import altair as alt
from datetime import datetime
import os

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="Air Quality Dashboard", layout="wide")

# ------------------ CUSTOM STYLING ------------------
st.markdown("""
    <style>
        html, body, .main {
            background-color: #001F3F;
            color: white;
        }
        .stApp {
            background-color: #001F3F;
        }
        .stButton > button {
            background-color: #007BFF;
            color: white;
        }
        .css-1y4p8pa.e1fqkh3o3, .css-1rs6os.edgvbvh3 {  /* Hide sidebar */
            display: none;
        }
        .css-18e3th9 { padding-top: 0rem; }
    </style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    st.image("ISRO-Color.png", width=80)
with col2:
    st.markdown("""
    <h2 style='text-align: center;'>ISRO & CPCB AIR QUALITY MONITORING</h2>
    <h4 style='text-align: center;'>Real-Time PM2.5 & PM10 Dashboard</h4>
    """, unsafe_allow_html=True)
with col3:
    st.image("cpcb.png", width=80)

st.markdown("---")

# ------------------ HIGH RESOLUTION PM2.5 MAP ------------------
st.subheader("🔍 High-Resolution PM2.5 Map")
hr_df = pd.read_csv("data/high_res_input_sample_100.csv")

hr_map = folium.Map(location=[hr_df['latitude'].mean(), hr_df['longitude'].mean()], zoom_start=5, tiles="CartoDB dark_matter")

for _, row in hr_df.iterrows():
    pm = row['PM2.5']
    color = 'green' if pm <= 60 else 'orange' if pm <= 120 else 'red'
    folium.CircleMarker(location=(row['latitude'], row['longitude']),
                        radius=4,
                        color=color,
                        fill=True,
                        fill_opacity=0.7).add_to(hr_map)

st_data = st_folium(hr_map, width=1000, height=500)

with st.expander("📊 View Data Table"):
    st.dataframe(hr_df)
    st.download_button("📥 Download High-Resolution CSV", hr_df.to_csv(index=False), file_name="high_res_pm25.csv")

# ------------------ CITY-WISE MONITORING ------------------
st.subheader("🏙️ City-wise PM2.5 & PM10 Monitoring")
cities = ["Delhi", "Bangalore", "Hyderabad", "Kolkata"]
city = st.selectbox("Select City", cities)

city_file_map = {
    "Delhi": "delhi_pm_data.csv",
    "Bangalore": "bangalore_pm_data.csv",
    "Hyderabad": "hyderabad_pm_data.csv",
    "Kolkata": "kolkata_pm_data.csv"
}

city_df = pd.read_csv(f"data/{city_file_map[city]}")
latest = city_df.iloc[-1]

col1, col2 = st.columns(2)
col1.metric("Latest PM2.5", f"{latest['PM2.5']:.1f} µg/m³")
col2.metric("Latest PM10", f"{latest['PM10']:.1f} µg/m³")

city_map = folium.Map(location=[city_df['latitude'].mean(), city_df['longitude'].mean()], zoom_start=10, tiles="CartoDB dark_matter")
folium.Marker(location=[latest['latitude'], latest['longitude']], tooltip=f"PM2.5: {latest['PM2.5']}, PM10: {latest['PM10']}").add_to(city_map)
st_folium(city_map, width=1000, height=400)

st.markdown("### 📈 10-Hour Pollution Trend")
trend_chart = alt.Chart(city_df.tail(10)).transform_fold(
    ["PM2.5", "PM10"],
    as_=["Type", "Value"]
).mark_line(point=True).encode(
    x="hour:O",
    y="Value:Q",
    color="Type:N"
).properties(height=300)

st.altair_chart(trend_chart, use_container_width=True)

# ------------------ COMBINED DOWNLOAD ------------------
st.markdown("---")
st.subheader("📥 Download Full City-Wise Data")
all_dfs = []
for city_name, filename in city_file_map.items():
    df = pd.read_csv(f"data/{filename}")
    df["City"] = city_name
    all_dfs.append(df)

combined_df = pd.concat(all_dfs, ignore_index=True)
st.download_button("Download Combined City Data", combined_df.to_csv(index=False), file_name="combined_city_data.csv")
