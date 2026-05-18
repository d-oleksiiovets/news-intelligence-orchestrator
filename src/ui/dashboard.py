import streamlit as st
from src.ui.views.geo_map_view import render_geo_map
from src.ui.views.time_series_view import render_time_series
from src.ui.views.metrics_overview import render_metrics_overview
from src.ui.views.bar_chart_view import render_bar_chart

st.set_page_config(page_title="News Sentiment", layout="wide")

def render_dashboard():
    st.title("Global News & Sentiment Analysis")
    st.divider()

    render_metrics_overview()

    tab_map, tab_bar, tab_time = st.tabs(["🗺️ Map", "📊 Charts", "📅 Timeline"])

    with tab_map:
        render_geo_map()

    with tab_time:
        render_time_series()

    with tab_bar:
        render_bar_chart()

if __name__ == "__main__":
    render_dashboard()