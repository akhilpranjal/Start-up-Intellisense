from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
import asyncio

from Analytics.agent import (
    ask_ecosystem,
)

from app_services import (
    get_overview,
    get_founding_year_trend,
    get_country_distribution,
    get_problem_domain_distribution,
    get_target_market_distribution,
    get_status_distribution,
    get_team_size_distribution,
    get_cluster_distribution,
    get_cluster_growth,
    get_emerging_clusters,
    get_clusters,
    get_cluster_members,
    get_landscape_points,
    semantic_search_wrapper,
)

 
# PAGE CONFIG
 

st.set_page_config(
    page_title="YC Startup Intelligence Platform",
    page_icon="🚀",
    layout="wide",
)

 
# SIDEBAR
 

st.sidebar.title("YC Startup Intelligence")

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Smart Search",
        "Cluster Explorer",
        "Startup Landscape",
        "Trend Discovery",
    ],
)

 
# OVERVIEW
 

if page == "Overview":

    st.title("YC Startup Intelligence Platform")

    overview = get_overview()

    if overview:

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Total Startups",
            overview.get("total_startups", 0),
        )

        c2.metric(
            "Countries",
            overview.get("countries", 0),
        )

        c3.metric(
            "Clusters",
            overview.get("clusters", 0),
        )

        c4.metric(
            "Average Team Size",
            round(
                overview.get(
                    "avg_team_size",
                    0,
                ),
                2,
            ),
        )

    st.divider()

     
    # Startup Formation Trend
     

    trend = get_founding_year_trend()

    if trend:

        st.subheader(
            "Startup Formation Trend"
        )

        df = pd.DataFrame(trend)

        fig = px.line(
            df,
            x="founded_year",
            y="count",
            markers=True,
        )

        st.plotly_chart(
            fig,
            width='stretch',
        )

    st.divider()

     
    # Countries + Clusters
     

    col1, col2 = st.columns(2)

    with col1:

        country_dist = (
            get_country_distribution()
        )

        if country_dist:

            st.subheader(
                "Top Countries"
            )

            df = pd.DataFrame(
                country_dist
            )

            fig = px.bar(
                df.head(20),
                x="country",
                y="count",
            )

            st.plotly_chart(
                fig,
                width='stretch',
            )

    with col2:

        cluster_dist = (
            get_cluster_distribution()
        )

        if cluster_dist:

            st.subheader(
                "Largest Clusters"
            )

            df = pd.DataFrame(
                cluster_dist
            )

            fig = px.bar(
                df.head(20),
                x="cluster_name",
                y="count",
            )

            st.plotly_chart(
                fig,
                width='stretch',
            )

    st.divider()

     
    # Startup Status + Team Size
     

    col1, col2 = st.columns(2)

    with col1:

        status_dist = (
            get_status_distribution()
        )

        if status_dist:

            st.subheader(
                "Startup Status Distribution"
            )

            df = pd.DataFrame(
                status_dist
            )

            fig = px.pie(
                df,
                names="status",
                values="count",
            )

            st.plotly_chart(
                fig,
                width='stretch',
            )

    with col2:

        team_sizes = (
            get_team_size_distribution()
        )

        if team_sizes:

            st.subheader(
                "Team Size Distribution"
            )

            df = pd.DataFrame(
                {
                    "team_size": team_sizes
                }
            )

            fig = px.histogram(
                df,
                x="team_size",
                nbins=30,
            )

            st.plotly_chart(
                fig,
                width='stretch',
            )

    st.divider()

     
    # Problem Domains + Target Markets
     

    col1, col2 = st.columns(2)

    with col1:

        domains = (
            get_problem_domain_distribution()
        )

        if domains:

            st.subheader(
                "Top Problem Domains"
            )

            df = pd.DataFrame(
                domains
            )

            fig = px.bar(
                df.head(15),
                x="problem_domain",
                y="count",
            )

            st.plotly_chart(
                fig,
                width='stretch',
            )

    with col2:

        markets = (
            get_target_market_distribution()
        )

        if markets:

            st.subheader(
                "Top Target Markets"
            )

            df = pd.DataFrame(
                markets
            )

            fig = px.bar(
                df.head(15),
                x="target_market",
                y="count",
            )

            st.plotly_chart(
                fig,
                width='stretch',
            )

 
# SMART SEARCH
 

elif page == "Smart Search":

    st.set_page_config(
    page_title="Ask Ecosystem",
    layout="wide",
    )

    st.title(
        "YC Ecosystem Analyst"
    )

    query = st.chat_input(
        "Ask anything..."
    )

    if query:

        with st.spinner(
            "Thinking..."
        ):

            result = asyncio.run(
                ask_ecosystem(
                    query
                )
            )

        if (
            result["intent"]
            == "company_search"
        ):

            st.subheader(
                "Companies"
            )

            for company in result[
                "results"
            ]:

                with st.container():

                    st.markdown(
                        f"""
    ### {company["name"]}

    {company["explanation"]}

    **Problem Domain:** {company["problem_domain"]}

    **Target Market:** {company["target_market"]}

    {company["website"]}
    """
                    )

        else:

            st.markdown(
                result["answer"]
            )

            with st.expander(
                "Sources"
            ):
                st.json(
                    result["sources"]
                )

 
# CLUSTER EXPLORER
 

elif page == "Cluster Explorer":

    st.title(
        "Cluster Explorer"
    )

    clusters = get_clusters()

    if not clusters:

        st.warning(
            "No clusters found."
        )
        st.stop()

    cluster_names = [
        c["cluster_name"]
        for c in clusters
    ]

    selected_name = st.selectbox(
        "Select Cluster",
        cluster_names,
    )

    selected_cluster = next(
        c
        for c in clusters
        if c["cluster_name"]
        == selected_name
    )

    st.subheader(
        selected_cluster[
            "cluster_name"
        ]
    )

    st.write(
        selected_cluster[
            "description"
        ]
    )

    st.metric(
        "Companies",
        selected_cluster[
            "company_count"
        ],
    )

    keywords = (
        selected_cluster.get(
            "keywords"
        )
        or []
    )

    if keywords:

        st.write("Keywords")

        st.write(
            ", ".join(keywords)
        )

    st.divider()

    members = get_cluster_members(
        selected_cluster[
            "cluster_id"
        ]
    )

    if members:

        st.subheader(
            "Cluster Members"
        )

        df = pd.DataFrame(
            members
        )

        st.dataframe(
            df,
            width='stretch',
        )

 
# STARTUP LANDSCAPE
 

elif page == "Startup Landscape":

    st.title(
        "Startup Landscape"
    )

    points = (
        get_landscape_points()
    )

    if not points:

        st.warning(
            "No UMAP coordinates found."
        )
        st.stop()

    df = pd.DataFrame(points)

    country_options = sorted(
        df["country"]
        .dropna()
        .unique()
    )

    selected_country = (
        st.selectbox(
            "Country",
            ["All"]
            + list(
                country_options
            ),
        )
    )

    if selected_country != "All":

        df = df[
            df["country"]
            == selected_country
        ]

    year_options = sorted(
        df["founded_year"]
        .dropna()
        .unique()
    )

    selected_year = (
        st.selectbox(
            "Founded Year",
            ["All"]
            + list(year_options),
        )
    )

    if selected_year != "All":

        df = df[
            df["founded_year"]
            == selected_year
        ]

    fig = px.scatter(
        df,
        x="umap_x",
        y="umap_y",
        color="cluster_id",
        hover_name="name",
        hover_data=[
            "country",
            "founded_year",
        ],
        title="Semantic Startup Universe",
    )

    st.plotly_chart(
        fig,
        width='stretch',
    )

 
# TREND DISCOVERY
 

elif page == "Trend Discovery":

    st.title(
        "Trend Discovery"
    )

    emerging = (
        get_emerging_clusters()
    )

    if emerging:

        st.subheader(
            "Emerging Clusters"
        )

        df = pd.DataFrame(
            emerging
        )

        fig = px.bar(
            df.head(15),
            x="cluster_name",
            y="growth_score",
        )

        st.plotly_chart(
            fig,
            width='stretch',
        )

    st.divider()

    cluster_growth = (
        get_cluster_growth()
    )

    if cluster_growth:

        st.subheader(
            "Cluster Growth Trends"
        )

        df = pd.DataFrame(
            cluster_growth
        )

        top_clusters = (
            df.groupby(
                "cluster_name"
            )["count"]
            .sum()
            .sort_values(
                ascending=False
            )
            .head(10)
            .index
        )

        df = df[
            df["cluster_name"]
            .isin(top_clusters)
        ]

        fig = px.line(
            df,
            x="founded_year",
            y="count",
            color="cluster_name",
        )

        st.plotly_chart(
            fig,
            width='stretch',
        )

    st.divider()

    domains = (
        get_problem_domain_distribution()
    )

    if domains:

        st.subheader(
            "Problem Domain Distribution"
        )

        df = pd.DataFrame(
            domains
        )

        fig = px.bar(
            df.head(20),
            x="problem_domain",
            y="count",
        )

        st.plotly_chart(
            fig,
            width='stretch',
        )