"""
app.py
Interactive application and map overlay interface using real clustering results.
Features: Time-based filtering, location-based suggestions, and restaurant descriptions.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time
import math
import numpy as np

st.set_page_config(
    page_title="NYC Restaurant Explorer", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# NYC Restaurant Recommendation System\nPowered by ML clustering and recommendation algorithms"
    }
)

# Custom CSS for better UI/UX
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #FF6B6B;
        --secondary-color: #4ECDC4;
        --accent-color: #FFE66D;
    }
    
    /* Title styling */
    h1 {
        color: #FF6B6B;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        font-size: 2.5em;
    }
    
    h2 {
        color: #4ECDC4;
        border-bottom: 2px solid #FF6B6B;
        padding-bottom: 10px;
    }
    
    h3 {
        color: #2C3E50;
    }
    
    /* Sidebar customization */
    .css-1d58rgt {
        background-color: #F7F9FC;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF5252 100%);
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(255, 107, 107, 0.3);
    }
    
    /* Info/Warning boxes */
    .stInfo {
        background-color: #E8F4F8;
        border-left: 4px solid #4ECDC4;
        border-radius: 8px;
        padding: 15px;
    }
    
    .stWarning {
        background-color: #FEF5E7;
        border-left: 4px solid #FFE66D;
        border-radius: 8px;
        padding: 15px;
    }
    
    /* Markdown links */
    a {
        color: #FF6B6B;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    try:
        # Load clustering results
        clusters_df = pd.read_csv("results/clustering/restaurant_clusters.csv")
        clusters_df = clusters_df.dropna(subset=['latitude', 'longitude'])
        clusters_df['cluster_label'] = clusters_df['cluster'].astype(str)
        
        # Load metadata with descriptions and hours
        meta_df = pd.read_parquet("data/processed/meta-NYC-restaurant.parquet")
        
        # Merge the two dataframes on gmap_id
        merged_df = pd.merge(clusters_df, meta_df[['gmap_id', 'description', 'hours', 'category', 'price', 'address', 'num_of_reviews']], 
                            on='gmap_id', how='left')
        
        return merged_df
    
    except Exception as e:
        st.error(f"Failed to load data. Please check the file path. Error: {e}")
        return pd.DataFrame()


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers (Haversine formula)"""
    R = 6371  # Earth's radius in kilometers
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def is_restaurant_open(hours_info, visit_date, visit_time):
    """Check if a restaurant is open at a specific time"""
    try:
        if hours_info is None or pd.isna(hours_info):
            return None
        
        # Convert to list if numpy array
        if isinstance(hours_info, np.ndarray):
            hours_list = hours_info.tolist()
        else:
            hours_list = hours_info
        
        # Get day of week name
        day_name = visit_date.strftime('%A')
        
        # Find matching day in hours list
        for entry in hours_list:
            if isinstance(entry, str):
                # Parse string format
                if 'Closed' in entry:
                    continue
                if day_name in entry:
                    # Extract time range
                    if '–' in entry:
                        parts = entry.split('–')
                        if len(parts) >= 2:
                            opening_str = parts[0].replace(day_name, '').strip()
                            closing_str = parts[1].strip()
                            
                            opening_time = parse_time_string(opening_str, closing_str)
                            closing_time = parse_time_string(closing_str)
                            
                            if opening_time and closing_time:
                                # Check for cross-day hours (e.g., 5PM–2AM)
                                is_cross_day = closing_time.hour < 6 or opening_time.hour >= 12
                                
                                # Reject illogical ranges like 11AM–10AM
                                if opening_time > closing_time and not is_cross_day:
                                    continue
                                
                                # Check if visit time is within range
                                if is_cross_day and closing_time < opening_time:
                                    # Overnight hours
                                    return visit_time >= opening_time or visit_time < closing_time
                                else:
                                    # Same day hours
                                    return opening_time <= visit_time <= closing_time
        
        return None
    
    except:
        return None


def parse_time_string(time_str, context_str=None):
    """Parse time string to time object"""
    try:
        time_str = str(time_str).strip().upper()
        
        # Handle 12AM and 12PM edge cases
        if time_str == '12AM' or time_str == '12:00AM':
            return time(0, 0)
        if time_str == '12PM' or time_str == '12:00PM':
            return time(12, 0)
        
        # Extract hour and minute
        hour = None
        minute = 0
        is_pm = None
        
        # Handle formats like "11AM", "5:30PM"
        if ':' in time_str:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute_part = parts[1].replace('AM', '').replace('PM', '').strip()
            minute = int(minute_part)
            is_pm = 'PM' in time_str
        else:
            # Handle formats like "11AM", "5PM"
            hour = int(''.join(c for c in time_str if c.isdigit()))
            is_pm = 'PM' in time_str
        
        # If no AM/PM specified, try to infer from context
        if is_pm is None:
            if context_str:
                is_pm = 'PM' in context_str.upper()
            else:
                is_pm = False
        
        # Convert to 24-hour format
        if is_pm and hour != 12:
            hour += 12
        elif not is_pm and hour == 12:
            hour = 0
        
        # If context has PM and current hour is small, assume PM
        if context_str and 'PM' in context_str.upper() and hour < 12:
            hour += 12
        
        return time(hour, minute)
    except:
        return None


st.title("🍕 NYC Restaurant Recommendation Map")

df = load_data()

if not df.empty:
    # Sidebar - Filters and Preferences
    st.sidebar.header("🎯 Filters & Preferences")
    
    # ===== NEW FEATURE: Time Selection =====
    st.sidebar.subheader("⏰ When do you want to go?")
    visit_date = st.sidebar.date_input("Select Date", value=datetime.now())
    visit_time = st.sidebar.time_input("Select Time", value=time(19, 0))
    
    # Display selection in teal box
    st.sidebar.markdown(f"""
    <div style="background-color: #4ECDC4; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <p style="color: white; margin: 0;"><b>🎯 Your Selection:</b></p>
        <p style="color: #FFE66D; font-size: 18px; margin: 5px 0;"><b>{visit_date.strftime('%A')} at {visit_time.strftime('%I:%M %p')}</b></p>
        <p style="color: white; font-size: 12px; margin: 5px 0;">({visit_time.strftime('%H:%M')} in 24-hour format)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== NEW FEATURE: Location-Based Search =====
    st.sidebar.subheader("📍 Location-Based Search")
    
    use_location = st.sidebar.checkbox("Enable location-based suggestions")
    
    location_lat = None
    location_lon = None
    
    if use_location:
        location_lat = st.sidebar.number_input("Your Latitude", value=40.7128, format="%.4f")
        location_lon = st.sidebar.number_input("Your Longitude", value=-74.0060, format="%.4f")
        
        # Distance radius filter
        max_distance = st.sidebar.slider("Maximum Distance (km)", 0.5, 15.0, 5.0, 0.5)
    
    filter_by_hours = st.sidebar.checkbox("🕐 Only show restaurants open at selected time", value=False)
    
    # Filter: Minimum Rating
    min_rating = st.sidebar.slider(
        "Minimum Rating Requirement", 
        min_value=1.0, 
        max_value=5.0, 
        value=3.5, 
        step=0.1
    )
    
    # Apply basic filters
    filtered_df = df[df['avg_rating'] >= min_rating]
    
    # Apply time-based filter if enabled
    if filter_by_hours:
        filtered_df['is_open'] = filtered_df['hours'].apply(
            lambda hours: is_restaurant_open(hours, visit_date, visit_time)
        )
        
        # Keep ONLY restaurants that are definitely open (True)
        filtered_df = filtered_df[filtered_df['is_open'] == True]
    
    # Apply location filter if enabled
    if use_location and location_lat is not None and location_lon is not None:
        filtered_df['distance_km'] = filtered_df.apply(
            lambda row: calculate_distance(location_lat, location_lon, row['latitude'], row['longitude']),
            axis=1
        )
        filtered_df = filtered_df[filtered_df['distance_km'] <= max_distance]
        filtered_df = filtered_df.sort_values('distance_km')
    
    # Display results in two columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🗺️ Restaurant Map")
        if not filtered_df.empty:
            fig = px.scatter_map(
                filtered_df, 
                lat="latitude", 
                lon="longitude", 
                color="cluster_label",   
                hover_name="name", 
                hover_data={"cluster_label": False, "avg_rating": True, "borough": True},
                color_discrete_sequence=px.colors.qualitative.Alphabet,
                zoom=10, 
                height=600
            )
            
            # Hide the cluster legend
            fig.update_traces(showlegend=False)
            
            # Add marker for user's location if location-based search is enabled
            if use_location and location_lat is not None and location_lon is not None:
                fig.add_scattermap(
                    lat=[location_lat],
                    lon=[location_lon],
                    mode='markers',
                    marker=dict(size=12, color='red', symbol='star'),
                    name='Your Location',
                    hovertemplate='<b>Your Location</b><extra></extra>'
                )
            
            fig.update_layout(map_style="carto-positron")
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, width='stretch', config={'scrollZoom': True})
        else:
            st.warning("No restaurants match the current filters. Please adjust the sidebar settings.")

    with col2:
        st.subheader("📋 Restaurant List")
        if not filtered_df.empty:
            # Display columns, including distance if location search is enabled
            display_columns = ['name', 'borough', 'avg_rating']
            if use_location and 'distance_km' in filtered_df.columns:
                display_columns.insert(2, 'distance_km')
            
            available_cols = [col for col in display_columns if col in filtered_df.columns]
            
            # Format distance if it exists
            display_df = filtered_df[available_cols].sort_values('avg_rating', ascending=False).copy()
            if 'distance_km' in display_df.columns:
                display_df['distance_km'] = display_df['distance_km'].apply(lambda x: f"{x:.1f} km")
            
            st.dataframe(display_df, height=600, width='stretch')
        else:
            st.info("No restaurants available with current filters.")

    # ===== NEW FEATURE: Detailed Restaurant Information =====
    st.divider()
    st.subheader("📍 Detailed Restaurant Information")
    
    if not filtered_df.empty:
        # Select a restaurant to view details
        selected_restaurant = st.selectbox(
            "Select a restaurant to view details:",
            options=filtered_df['name'].tolist()
        )
        
        if selected_restaurant:
            restaurant_info = filtered_df[filtered_df['name'] == selected_restaurant].iloc[0]
            
            # Create two columns for better layout
            info_col1, info_col2 = st.columns(2)
            
            with info_col1:
                st.markdown(f"**🍽️ Restaurant Name:** {restaurant_info['name']}")
                st.markdown(f"**⭐ Rating:** {restaurant_info['avg_rating']} / 5")
                
                # Number of Reviews with safe handling
                try:
                    num_reviews = restaurant_info['num_of_reviews']
                    if pd.notna(num_reviews) and str(num_reviews) != 'nan':
                        st.markdown(f"**📞 Number of Reviews:** {int(float(num_reviews))}")
                    else:
                        st.markdown(f"**📞 Number of Reviews:** N/A")
                except:
                    st.markdown(f"**📞 Number of Reviews:** N/A")
                
                st.markdown(f"**🏢 Borough:** {restaurant_info['borough']}")
                
                # Price Level with safe handling
                try:
                    price = restaurant_info['price']
                    price_str = str(price) if price is not None else 'N/A'
                    if price_str and price_str != 'N/A' and price_str.strip() and price_str != 'nan':
                        st.markdown(f"**💰 Price Level:** {price_str}")
                except:
                    pass
                
                # Category with safe handling
                try:
                    category = restaurant_info['category']
                    # Convert numpy array to comma-separated string
                    if isinstance(category, np.ndarray):
                        cat_str = ', '.join([str(c).strip("'\"") for c in category])
                    else:
                        cat_str = str(category)
                    
                    if cat_str and cat_str != 'nan' and cat_str.strip():
                        st.markdown(f"**📂 Category:** {cat_str}")
                except:
                    pass
            
            with info_col2:
                if use_location and 'distance_km' in restaurant_info:
                    st.markdown(f"**📏 Distance from You:** {restaurant_info['distance_km']:.1f} km")
            
            # Address
            st.markdown(f"**🏠 Address:** {restaurant_info.get('address', 'N/A')}")
            
            # Opening Hours - robust handling
            try:
                hours_info = restaurant_info['hours']
                
                if hours_info is not None and not pd.isna(hours_info):
                    if isinstance(hours_info, np.ndarray):
                        hours_list = hours_info.tolist()
                    else:
                        hours_list = hours_info
                    
                    st.markdown("**🕐 Hours:**")
                    for hour_entry in hours_list:
                        st.markdown(f"- {hour_entry}")
            except:
                st.markdown("**🕐 Hours:** N/A")
            
            # Description
            try:
                description = restaurant_info.get('description', 'N/A')
                if description is not None and str(description) != 'nan':
                    st.markdown(f"**📝 Description:**\n{description}")
            except:
                pass
    
    st.divider()
    st.subheader("💡 About This App")
    st.info("Select filters on the left to discover restaurants by rating, location, and more!")
