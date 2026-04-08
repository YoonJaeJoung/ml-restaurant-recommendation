"""
app.py
Interactive application and map overlay interface using real clustering results.
"""
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="NYC Restaurant Explorer", layout="wide")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("results/clustering/restaurant_clusters.csv")
        df = df.dropna(subset=['latitude', 'longitude'])
        
        # Convert cluster to string so that Plotly treats it as a categorical variable (discrete colors) instead of a continuous gradient
        df['cluster_label'] = df['cluster'].astype(str)
            
        return df
    
    except Exception as e:
        st.error(f"Failed to load data. Please check the file path. Error: {e}")
        return pd.DataFrame()


st.title("🍕 NYC Restaurant Recommendation Map")

df = load_data()

if not df.empty:
    # Sidebar - Used for filters
    st.sidebar.header("🎯 Filters")
    
    # Filter: Select Cluster
    # Sort numerically first to ensure sidebar options are 0, 1, 2, 3... instead of 0, 1, 10, 11...
    clusters_numeric = sorted(df['cluster'].unique().tolist())
    
    selected_cluster = st.sidebar.multiselect(
        "Select Restaurant Category (Cluster)", 
        options=clusters_numeric, 
        default=clusters_numeric[:5] # Default to showing the first 5 clusters to prevent lag during initial map loading
    )
    
    # Filter: Minimum Rating
    min_rating = st.sidebar.slider(
        "Minimum Rating Requirement", 
        min_value=1.0, 
        max_value=5.0, 
        value=3.5, 
        step=0.1
    )
    
    # Apply filters
    filtered_df = df[(df['cluster'].isin(selected_cluster)) & (df['avg_rating'] >= min_rating)]
    
    st.sidebar.markdown(f"**Total matching restaurants: {len(filtered_df)}**")

    # Main Layout (Two columns: Map on the left, List on the right)
    col1, col2 = st.columns([2, 1]) # Left: 2/3 for Map, Right: 1/3 for List

    with col1:
        st.subheader("🗺️ Restaurant Distribution Map")
        if not filtered_df.empty:
            # 🌟 Use discrete colors for plotting and add borough information
            fig = px.scatter_mapbox(
                filtered_df, 
                lat="latitude", 
                lon="longitude", 
                color="cluster_label",   
                hover_name="name", 
                hover_data={"cluster_label": False, "cluster": True, "avg_rating": True, "borough": True}, # Information to display on hover
                color_discrete_sequence=px.colors.qualitative.Alphabet, # Palette suitable for multiple categories
                zoom=10, 
                height=600
            )
            fig.update_layout(mapbox_style="carto-positron") 
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
        else:
            st.warning("No restaurants match the current filters. Please adjust the sidebar settings.")

    with col2:
        st.subheader("📋 Restaurant Details List")
        display_columns = ['name', 'borough', 'avg_rating', 'cluster']
        available_cols = [col for col in display_columns if col in filtered_df.columns]
        
        st.dataframe(filtered_df[available_cols].sort_values('avg_rating', ascending=False), height=600, use_container_width=True)

    # Placeholder for future "Recommendation System" features
    st.divider()
    st.subheader("💡 Smart Recommendation")
    st.info("Coming Soon: We will integrate similarity-based recommendations using Embedding vectors! You will be able to input a restaurant you like and find the most similar ones.")
