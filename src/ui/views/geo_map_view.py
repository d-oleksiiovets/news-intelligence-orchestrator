import streamlit as st
import plotly.express as px
from src.services.data_queries import fetch_map_and_news_data, fetch_events_list

def render_geo_map():
    event_dict = fetch_events_list()
    options = ["ALL"] + list(event_dict.keys())

    selected_event = st.selectbox(
        "Select Topic:", 
        options, 
        format_func=lambda x: "All Events" if x == "ALL" else event_dict[x]
    )
    
    map_df, news_df = fetch_map_and_news_data(selected_event)

    fig = px.choropleth(
        map_df,
        locations="iso_code",
        color="avg_sentiment",
        hover_name="name",
        hover_data={"iso_code": False, "mentions": True, "avg_sentiment": ':.2f'},
        color_continuous_scale="RdYlGn",
        range_color=[-1, 1]
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    selection = st.plotly_chart(fig, on_select="rerun", selection_mode="points")

    selected_iso_code = None
    if selection and selection["selection"]["points"]:
        selected_iso_code = selection["selection"]["points"][0]["location"]

    st.divider()

    if selected_iso_code:
        country_row = map_df[map_df['iso_code'] == selected_iso_code].iloc[0]
        country_news = news_df[news_df['iso_code'] == country_row['iso_code']]

        st.subheader(f"News: {country_row['name']}")
        st.write(f"**Mentions:** {country_row['mentions']} | **Sentiment:** {country_row['avg_sentiment']:.2f}")

        for _, row in country_news.iterrows():
            with st.container(border=True):
                st.markdown(f"**[{row['title']}]({row['url']})**")
                st.caption(f"{row['source_name']} · {row['published_at']}")
    else:
        st.info("Click a country to see news.")