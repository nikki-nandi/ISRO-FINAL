import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt
import os
import time

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="PM2.5 & PM10 Dashboard", layout="wide")

# ------------------ DARK UI CSS ------------------
st.markdown("""
    <style>
    .main { background-color: #0b1725; color: white; }
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
    </style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
col1, col2, col3 = st.columns([1, 5, 1])
with col1:
    st.image("ISRO-Color.png", width=120)
with col2:
    st.markdown("""
        <h2 style='text-align: center; color: #64b5f6;'>ISRO & CPCB AIR POLLUTION MONITORING</h2>
        <h5 style='text-align: center; color: #a5b4c3;'>Live PM2.5 & PM10 Dashboard</h5>
    """, unsafe_allow_html=True)
with col3:
    st.image("cpcb.png", width=120)

st.markdown("---")

# ------------------ COLOR FUNCTION ------------------
def get_pm_color(pm):
    if pm <= 60:
        return [0, 200, 0]
    elif pm <= 120:
        return [255, 165, 0]
    else:
        return [255, 0, 0]

# ------------------ SECTION 1: HIGH-RESOLUTION MAP ------------------
st.markdown("### 🛰️ High-Resolution PM2.5 Map")

@st.cache_data
def load_highres():
    df = pd.read_csv("data/high_res_pm25_predictions.csv")
    df.columns = df.columns.str.lower().str.replace(".", "", regex=False).str.replace(" ", "")
    return df

df_map = load_highres()
df_map["color"] = df_map["pm25_pred"].apply(get_pm_color)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position='[longitude, latitude]',
    get_radius=10000,
    get_fill_color="color",
    pickable=True,
    opacity=0.8,
)

view = pdk.ViewState(latitude=22.5, longitude=80, zoom=4.5, pitch=40)

st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/dark-v10",  # ✅ Black map
    initial_view_state=view,
    layers=[layer],
    tooltip={"text": "Lat: {latitude}\nLon: {longitude}\nPM2.5: {pm25_pred}"}
))

with st.expander("📋 Show Prediction Table"):
    st.dataframe(df_map[["latitude", "longitude", "pm25_pred"]].round(2))

st.download_button("📥 Download High-Res Predictions",
                   df_map.to_csv(index=False).encode(),
                   "high_res_pm25_predictions.csv",
                   "text/csv")

st.markdown("---")

# ------------------ SECTION 2: CITY-WISE MONITORING ------------------
st.markdown("### 🌆 City-Wise Real-Time PM2.5 & PM10 Monitoring")

city_files = {
    "Delhi": "data/delhi_pm_data.csv",
    "Bangalore": "data/bangalore_pm_data.csv",
    "Hyderabad": "data/hyderabad_pm_data.csv",
    "Kolkata": "data/kolkata_pm_data.csv"
}

st.sidebar.header("🔧 Configuration")
selected_cities = st.sidebar.multiselect("Select Cities", list(city_files.keys()), default=list(city_files.keys()))
refresh_interval = st.sidebar.selectbox("Refresh Interval (sec)", [1, 5, 10], index=1)

frames = []
for city in selected_cities:
    path = city_files[city]
    if os.path.exists(path):
        df = pd.read_csv(path)
        df.columns = df.columns.str.lower().str.replace(".", "", regex=False).str.replace(" ", "")
        df["city"] = city
        frames.append(df)
    else:
        st.warning(f"Data for {city} not found.")

if not frames:
    st.stop()

df_all = pd.concat(frames, ignore_index=True)

# ------------------ LIVE DISPLAY LOOP ------------------
placeholder = st.empty()

for i in range(len(df_all)):
    row = df_all.iloc[i]

    with placeholder.container():
        st.markdown(f"### 🏙️ {row['city']} | ⏱️ Hour: {int(row['hour'])}")

        col1, col2 = st.columns(2)
        col1.markdown(f"""
            <div style='padding:20px;background:#112233;color:white;border-radius:10px;'>
            PM2.5<br><span style='font-size:36px'>{row['pm25_pred']:.2f}</span></div>
        """, unsafe_allow_html=True)
        col2.markdown(f"""
            <div style='padding:20px;background:#112233;color:white;border-radius:10px;'>
            PM10<br><span style='font-size:36px'>{row['pm10_pred']:.2f}</span></div>
        """, unsafe_allow_html=True)

        map_view = pdk.ViewState(latitude=row["latitude"], longitude=row["longitude"], zoom=6, pitch=40)
        map_layer = pdk.Layer("ScatterplotLayer", data=pd.DataFrame([row]),
                              get_position='[longitude, latitude]',
                              get_fill_color=get_pm_color(row["pm25_pred"]),
                              get_radius=10000)

        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/dark-v10",
            initial_view_state=map_view,
            layers=[map_layer],
            tooltip={"text": "Lat: {latitude}\nLon: {longitude}\nPM2.5: {pm25_pred}\nPM10: {pm10_pred}"}
        ))

        last_10 = df_all[df_all["city"] == row["city"]].copy().tail(10)
        melted = pd.melt(last_10, id_vars=["hour"], value_vars=["pm25_pred", "pm10_pred"],
                         var_name="Pollutant", value_name="Concentration")

        chart = alt.Chart(melted).mark_line(point=True).encode(
            x=alt.X("hour:O", title="Hour"),
            y=alt.Y("Concentration:Q", title="μg/m³"),
            color=alt.Color("Pollutant:N"),
            tooltip=["hour", "Pollutant", "Concentration"]
        ).properties(title="📊 Last 10 Readings", height=300, width=800)

        st.altair_chart(chart, use_container_width=True)
        st.markdown("---")

    time.sleep(refresh_interval)

# ------------------ FINAL DOWNLOAD ------------------
st.download_button("📥 Download All City Predictions",
                   df_all.to_csv(index=False).encode(),
                   "all_city_pm_predictions.csv",
                   "text/csv")
