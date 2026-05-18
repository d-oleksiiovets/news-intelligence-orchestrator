import streamlit as st
from src.services.data_queries import fetch_metrics

def render_metrics_overview():
    metrics = fetch_metrics()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total number of news", metrics["total_events"])
    col2.metric(f"Global sentiment", f"{metrics['avg_sentiment']:.2f}")
    col3.metric(f"Сountries in analysis", metrics["unique_countries"])