import streamlit as st
import plotly.express as px
from src.services.data_queries import fetch_barchart_data

def render_bar_chart():
    barchart_df = fetch_barchart_data()

    top_n = st.slider("Top N countries", 5, 30, 15, key="global_bar_top_n")
    top = barchart_df.nlargest(top_n, "mentions")
    worst = barchart_df.nsmallest(top_n, "avg_sentiment")
    best = barchart_df.nlargest(top_n, "avg_sentiment")

    col_chart, col_pie = st.columns([2, 1])

    with col_chart:
        st.subheader("Top Countries by Mentions")
        fig_bar = px.bar(
            top,
            x="name",
            y="mentions",
            color="avg_sentiment",
            color_continuous_scale="RdYlGn",
            range_color=[-1, 1],
            labels={"name": "Country", "mentions": "Mentions", "avg_sentiment": "Sentiment"},
        )
        fig_bar.update_layout(
            xaxis_tickangle=-35,
            margin={"t": 20, "b": 0},
            coloraxis_colorbar=dict(title="Sentiment"),
            paper_bgcolor="rgba(0,0,0,0)",   
            plot_bgcolor="#1e1e2e"
        )
        fig_bar.update_traces(
            hovertemplate=
            "Country: %{x}<br>" +
            "Mentions: %{y}<br>" +
            "Sentiment: %{marker.color:.2f}<extra></extra>"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_pie:
        st.subheader("Mention Share")
        fig_pie = px.pie(
            top,
            names="name",
            values="mentions",
            hole=0.4,
        )
        fig_pie.update_traces(
            hovertemplate=
            "Country: %{label}<br>" +
            "Mentions: %{value:.2f}<br>" +
            "Share: %{percent:.2%}<extra></extra>"
        )
        fig_pie.update_layout(
            margin={"t": 20, "b": 0}, showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",   
            plot_bgcolor="#1e1e2e"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    st.subheader(f"Top {top_n} countries with the worst sentiment")
    fig = px.bar(
        worst,
        x="name",
        y="avg_sentiment",
        color="avg_sentiment",              
        color_continuous_scale="RdYlGn",    
        range_color=[-1, 1],                
        text="avg_sentiment",
        labels={"name": "Country", "avg_sentiment": "Sentiment"},
    )

    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",

        hovertemplate=
        "Country: %{label}<br>" +
        "Mentions: %{value:.2f}<extra></extra>"
    )

    fig.update_layout(
        xaxis_tickangle=-35,
        margin={"t": 20, "b": 0},
        coloraxis_showscale=False,     
        yaxis=dict(range=[-1, 1]),

        paper_bgcolor="rgba(0,0,0,0)",   
        plot_bgcolor="#1e1e2e"
    )                                       
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader(f"Top {top_n} countries with the best sentiment")
    fig = px.bar(
        best,
        x="name",
        y="avg_sentiment",
        color="avg_sentiment",              
        color_continuous_scale="RdYlGn",    
        range_color=[-1, 1],                
        text="avg_sentiment",
        labels={"name": "Country", "avg_sentiment": "Sentiment"},
    )

    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",

        hovertemplate=
        "Country: %{label}<br>" +
        "Mentions: %{value:.2f}<extra></extra>"
    )

    fig.update_layout(
        xaxis_tickangle=-35,                
        margin={"t": 20, "b": 0},
        coloraxis_showscale=False,          
        yaxis=dict(range=[-1, 1]),

        paper_bgcolor="rgba(0,0,0,0)",   
        plot_bgcolor="#1e1e2e"    
    )                                       
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Mentions vs Sentiment")
    fig_scatter = px.scatter(
        barchart_df,
        x="mentions",
        y="avg_sentiment",
        hover_name="name",
        size="mentions",
        color="avg_sentiment",
        color_continuous_scale="RdYlGn",
        range_color=[-1, 1],
        labels={"mentions": "Mentions", "avg_sentiment": "Avg Sentiment"},
    )
    fig_scatter.update_traces(
        hovertemplate=
        "Country: %{hovertext}<br>" +
        "Mentions: %{x}<br>" +
        "Sentiment: %{marker.color:.2f}<extra></extra>"
    )
    fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig_scatter.update_layout(
        margin={"t": 20},
        paper_bgcolor="rgba(0,0,0,0)",   
        plot_bgcolor="#1e1e2e"
        )
    st.plotly_chart(fig_scatter, use_container_width=True)

