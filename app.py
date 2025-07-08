# Streamlit app to visualize precomputed air quality data using CSV files
import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt
import time
import os

# Page config
st.set_page_config(page_title="PM2.5 & PM10 Monitoring", layout="wide")

# --- BLUE THEME STYLING ---
st.markdown("""
    <style>
    .main {
        background-color: #0b1f3a;
        color: #ffffff;
    }
    section[data-testid="stSidebar"] {
        background-color: #0b1f3a;
        color: white;
        border-right: 1px solid #0b3c5d;
    }
    h1, h2, h3, h4, .st-bb, .st-cb {
        color: #ffffff !important;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #1e88e5;
        color: white;
        font-weight: bold;
        border-radius: 8px;
    }
    .block-container {
        background-color: #0b1f3a;
    }
    .stDataFrame {
        background-color: #0b1f3a !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
col1, col2, col3 = st.columns([1, 5, 1])
with col2:
    st.markdown("""
        <h2 style='text-align: center; color: #64b5f6;'>ISRO & CPCB AIR POLLUTION MONITORING</h2>
        <h5 style='text-align: center; color: #a5b4c3;'>PM2.5 / PM10 Predictions from CSV Files</h5>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- COLOR FUNCTION ---
def get_pm_color(pm):
    if pm <= 60:
        return [0, 200, 0]
    elif pm <= 120:
        return [255, 165, 0]
    else:
        return [255, 0, 0]

# --- LOAD HIGH-RES MAP DATA ---
st.markdown("### 🌏 High-Resolution PM2.5 Prediction Map")
high_res_path = "data/high_res_predicted.csv"
if os.path.exists(high_res_path):
    df_map = pd.read_csv(high_res_path)
    df_map["color"] = df_map["PM2.5_Predicted"].apply(get_pm_color)

    layer_map = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position='[longitude, latitude]',
        get_radius=10000,
        get_fill_color="color",
        pickable=True,
        opacity=0.8,
    )

    view_map = pdk.ViewState(latitude=22.5, longitude=80.0, zoom=4.5, pitch=40)

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v10",
        initial_view_state=view_map,
        layers=[layer_map],
        tooltip={"text": "Lat: {latitude}\nLon: {longitude}\nPM2.5: {PM2.5_Predicted}"}
    ))

    with st.expander("📋 Show Prediction Table"):
        st.dataframe(df_map.round(2))

    st.download_button("Download High-Res Predictions", data=df_map.to_csv(index=False), file_name="high_res_pm25.csv")
else:
    st.warning("High-resolution CSV not found.")

# --- MONITOR CITY-WISE LIVE DATA ---
st.markdown("### 🌐 Multi-City PM2.5 & PM10 Monitoring")
city_files = {
    "Delhi": "data/delhi_pm_data.csv",
    "Bangalore": "data/bangalore_pm_data.csv",
    "Hyderabad": "data/hyderabad_pm_data.csv"
}

selected_cities = st.sidebar.multiselect("Select Cities to Monitor", list(city_files.keys()), default=list(city_files.keys()))
refresh_interval = st.sidebar.selectbox("Refresh Interval (s)", [1, 2, 5], index=1)

placeholder = st.empty()

frames = []
for city in selected_cities:
    path = city_files.get(city)
    if path and os.path.exists(path):
        df = pd.read_csv(path)
        df["city"] = city
        frames.append(df)

if frames:
    df_all = pd.concat(frames, ignore_index=True)

    for i in range(len(df_all)):
        row = df_all.iloc[i]

        with placeholder.container():
            st.markdown(f"### 🌆 {row['city']} | Hour: {int(row['hour'])}")
            col1, col2 = st.columns(2)
            col1.metric("PM2.5 (Predicted)", f"{row['PM2.5_pred']:.2f} μg/m³")
            col2.metric("PM10 (Predicted)", f"{row['PM10_pred']:.2f} μg/m³")

            # Map
            view = pdk.ViewState(latitude=row["latitude"], longitude=row["longitude"], zoom=6, pitch=40)
            layer = pdk.Layer("ScatterplotLayer", data=pd.DataFrame([row]),
                              get_position='[longitude, latitude]',
                              get_fill_color=get_pm_color(row["PM2.5_pred"]),
                              get_radius=10000)

            st.pydeck_chart(pdk.Deck(map_style="mapbox://styles/mapbox/dark-v10",
                                     initial_view_state=view,
                                     layers=[layer]))

            # Last 10 points chart
            city_df = df_all[df_all.city == row.city].tail(10)
            melted = pd.melt(city_df, id_vars=["hour"],
                             value_vars=["PM2.5_pred", "PM10_pred"],
                             var_name="Pollutant", value_name="Value")

            chart = alt.Chart(melted).mark_line(point=True).encode(
                x=alt.X("hour:O"),
                y=alt.Y("Value:Q"),
                color="Pollutant:N",
                tooltip=["hour", "Pollutant", "Value"]
            ).properties(height=300)

            st.altair_chart(chart, use_container_width=True)
            st.markdown("---")

        time.sleep(refresh_interval)

    st.download_button("Download All City Data", data=df_all.to_csv(index=False), file_name="city_monitor_data.csv")
else:
    st.warning("No city data available.")
