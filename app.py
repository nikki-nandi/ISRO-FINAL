import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import altair as alt

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="ISRO & CPCB Air Pollution Live Monitoring", layout="wide")

# ------------------ CUSTOM CSS ------------------
st.markdown("""
    <style>
        body, .main, .stApp {
            background-color: #001F3F;
            color: white;
        }
        h1, h2, h3, h4, h5, h6 {
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    st.image("ISRO-Color.png", width=80)
with col2:
    st.markdown("""
        <h2 style='text-align: center;'>ISRO & CPCB AIR POLLUTION LIVE MONITORING SITE</h2>
        <h5 style='text-align: center;'>Real-Time Air Quality Monitoring</h5>
    """, unsafe_allow_html=True)
with col3:
    st.image("cpcb.png", width=80)

st.markdown("---")

# ------------------ SIDEBAR ------------------
st.sidebar.header("🛠️ Configuration")
selected_cities = st.sidebar.multiselect(
    "Select cities to monitor:",
    ["Delhi", "Kolkata", "Bangalore", "Hyderabad"],
    default=["Delhi"]
)
refresh_interval = st.sidebar.selectbox(
    "Refresh Interval (seconds)",
    [5, 10, 30, 60],
    index=1
)

# ------------------ HIGH-RES MAP ------------------
st.subheader("🌍 High-Resolution PM2.5 Prediction Map")

try:
    hr_df = pd.read_csv("data/high_res_input_sample_100.csv")
except Exception:
    st.warning("High-resolution file not found. Showing dummy data.")
    hr_df = pd.DataFrame({
        "latitude": [28.6, 19.07],
        "longitude": [77.2, 72.87],
        "PM2.5": [50, 110]
    })

hr_map = folium.Map(
    location=[hr_df['latitude'].mean(), hr_df['longitude'].mean()],
    zoom_start=5,
    tiles="CartoDB dark_matter"
)

for _, row in hr_df.iterrows():
    pm = row['PM2.5']
    color = 'green' if pm <= 60 else 'orange' if pm <= 120 else 'red'
    folium.CircleMarker(
        location=(row['latitude'], row['longitude']),
        radius=4,
        color=color,
        fill=True,
        fill_opacity=0.7
    ).add_to(hr_map)

folium_static(hr_map, width=1200, height=500)

if st.button("📊 Show High-Resolution Prediction Table"):
    st.dataframe(hr_df)

st.download_button(
    "📥 Download High-Res Predictions",
    hr_df.to_csv(index=False),
    file_name="high_res_pm25.csv"
)

# ------------------ CITY-WISE MONITORING ------------------

st.subheader("📡 Multi-City Live PM2.5 & PM10 Monitoring Dashboard")

city_file_map = {
    "Delhi": "delhi_pm_data.csv",
    "Kolkata": "kolkata_pm_data.csv",
    "Bangalore": "bangalore_pm_data.csv",
    "Hyderabad": "hyderabad_pm_data.csv"
}

if selected_cities:
    for city in selected_cities:
        st.markdown(f"### 🏙️ {city}")

        file_name = city_file_map[city]
        try:
            df = pd.read_csv(f"data/{file_name}")
        except Exception:
            st.warning(f"No data for {city}. Showing dummy data.")
            df = pd.DataFrame({
                "hour": list(range(1, 11)),
                "PM2.5": [40 + i*2 for i in range(10)],
                "PM10": [70 + i*3 for i in range(10)],
                "latitude": [28.6]*10,
                "longitude": [77.2]*10
            })

        latest = df.iloc[-1]

        st.markdown(f"**Hour:** {latest['hour']}")

        c1, c2 = st.columns(2)
        c1.metric("PM2.5", f"{latest['PM2.5']:.2f}")
        c2.metric("PM10", f"{latest['PM10']:.2f}")

        city_map = folium.Map(
            location=[latest['latitude'], latest['longitude']],
            zoom_start=10,
            tiles="CartoDB dark_matter"
        )
        folium.Marker(
            location=[latest['latitude'], latest['longitude']],
            tooltip=f"PM2.5: {latest['PM2.5']}, PM10: {latest['PM10']}"
        ).add_to(city_map)

        folium_static(city_map, width=1200, height=400)

        st.markdown("### ⏱️ Last 10 Readings")
        chart = alt.Chart(df.tail(10)).transform_fold(
            ["PM2.5", "PM10"], as_=["Pollutant", "Value"]
        ).mark_line(point=True).encode(
            x="hour:O",
            y="Value:Q",
            color="Pollutant:N"
        ).properties(height=300)

        st.altair_chart(chart, use_container_width=True)
else:
    st.info("Please select at least one city to monitor.")

# ------------------ COMBINED DOWNLOAD ------------------

st.markdown("---")
st.subheader("📦 Download All Cities Data")

all_dfs = []
for city_name, file_name in city_file_map.items():
    try:
        df = pd.read_csv(f"data/{file_name}")
    except Exception:
        df = pd.DataFrame({
            "hour": list(range(1, 11)),
            "PM2.5": [40 + i*2 for i in range(10)],
            "PM10": [70 + i*3 for i in range(10)],
            "latitude": [28.6]*10,
            "longitude": [77.2]*10
        })
    df["City"] = city_name
    all_dfs.append(df)

combined_df = pd.concat(all_dfs, ignore_index=True)

st.download_button(
    "📥 Download All Cities Data",
    combined_df.to_csv(index=False),
    file_name="all_cities_data.csv"
)
