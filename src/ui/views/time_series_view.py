import streamlit as st
import plotly.graph_objects as go

from src.services.data_queries import fetch_timeline_data, fetch_mix_max_date

def render_time_series(selected_event: str = "ALL"):    
    min_date, max_date = fetch_mix_max_date() 

    col_date, col_grain = st.columns([3, 1])

    with col_date:
        date_range = st.date_input(
            "Period",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="time_date_range"
        )

    with col_grain:
        granularity = st.selectbox(
            "Granularity",
            ["Day", "Week", "Month"],
            key="time_granularity"
        )

    show_sentiment = st.checkbox("Show sentiment", value=True, key="time_show_sent")

    start_date, end_date = None, None
    if len(date_range) == 2:
        start_date, end_date = date_range
    elif len(date_range) == 1:
        start_date = date_range[0]
        end_date = date_range[0]

    grain_map = {"Day": "day", "Week": "week", "Month": "month"}
    sql_freq = grain_map[granularity]

    df_time = fetch_timeline_data(
        freq=sql_freq, 
        start_date=start_date, 
        end_date=end_date,
        event_id=selected_event
    )

    if df_time.empty:
        st.info("No news in selected period.")
        return
    
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_time["date"],
        y=df_time["news_count"],
        name="Articles",
        marker_color="#6366f1",
        opacity=0.7,
        yaxis="y1"
    ))

    if show_sentiment:
        fig.add_trace(go.Scatter(
            x=df_time["date"],
            y=df_time["avg_sentiment"],
            name="Avg sentiment",
            line=dict(color="#22c55e", width=2),
            mode="lines+markers",
            marker=dict(size=5),
            yaxis="y2",
            hovertemplate="Avg Sentiment: %{y:.2f}<extra></extra>"
        ))
        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="gray",
            opacity=0.4,
            yref="y2"
        )

    fig.update_layout(
        yaxis=dict(title="Articles"),
        yaxis2=dict(
            title="Sentiment" if show_sentiment else "",
            overlaying="y",
            side="right",
            range=[-1, 1],
            showgrid=False,
            visible=show_sentiment,
        ),
        legend=dict(orientation="h", y=1.1),
        margin={"t": 30, "b": 0},
        hovermode="x unified",
    )

    st.subheader("News Volume Over Time")
    st.plotly_chart(fig, use_container_width=True)