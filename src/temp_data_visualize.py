import streamlit as st
import pandas as pd
import pydeck as pdk
import datetime

st.set_page_config(layout="wide", page_title="NYC Restaurant Explorer")

@st.cache_data
def load_meta():
    df = pd.read_parquet("data/processed/meta-NYC-restaurant.parquet")
    # Ensure coordinates are numeric
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df = df.dropna(subset=['latitude', 'longitude'])
    
    # Safely format complex metadata (numpy arrays/lists from PyArrow)
    def format_field(x):
        try:
            if hasattr(x, '__iter__') and not isinstance(x, str):
                return ', '.join(map(str, x))
            if pd.isna(x):
                return 'N/A'
        except Exception:
            pass # ValueError happens if pd.isna is called on an array, meaning it's not a single NaN
        return str(x)

    df['tooltip_category'] = df['category'].apply(format_field)
    df['tooltip_price'] = df['price'].fillna('N/A')
    # df['tooltip_hours'] = df['hours'].apply(format_field)
    df['tooltip_desc'] = df['description'].fillna('No description')
    
    return df

@st.cache_data
def get_restaurant_reviews(gmap_id):
    # Only read the reviews for the selected restaurant using PyArrow's pushdown filters
    # This avoids loading the entire 750MB dataset into memory which slows down Streamlit
    df = pd.read_parquet(
        "data/processed/review-NYC-restaurant.parquet",
        filters=[('gmap_id', '==', gmap_id)]
    )
    return df

st.title("🗽 NYC Restaurant Explorer")
st.markdown("Explore restaurants on the map. **Hover** for details, and **click** a marker to view its reviews!")

with st.spinner("Loading data..."):
    df_meta = load_meta()

# Map Configuration
tooltip = {
    "html": "<b>{name}</b><br/>"
            "<b>Category:</b> {tooltip_category}<br/>"
            "<b>Price:</b> {tooltip_price}<br/>"
            # "<b>Hours:</b> {tooltip_hours}<br/>"
            "<hr/><i>{tooltip_desc}</i>",
    "style": {
        "backgroundColor": "white",
        "color": "black",
        "border": "2px solid black",
        "borderRadius": "10px",
        "padding": "10px",
        "fontFamily": "sans-serif",
        "whiteSpace": "normal",
        "width": "250px",
        "wordWrap": "break-word"
    }
}

# Pass only the string/float columns to pydeck to avoid complex object serialization errors
cols_to_keep = ['name', 'latitude', 'longitude', 'gmap_id', 
                'tooltip_category', 'tooltip_price', 'tooltip_hours', 'tooltip_desc']
df_map = df_meta[[c for c in cols_to_keep if c in df_meta.columns]]

layer = pdk.Layer(
    'ScatterplotLayer',
    data=df_map,
    get_position='[longitude, latitude]',
    get_color='[200, 30, 0, 160]',
    get_radius=50,
    radius_min_pixels=5,
    radius_max_pixels=5,
    pickable=True,
    auto_highlight=True,
    id='restaurants'
)

view_state = pdk.ViewState(
    latitude=40.7128,
    longitude=-74.0060,
    zoom=11,
    pitch=0
)

r = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip=tooltip,
    map_style=None # Defaults to Streamlit Carto style which is visible without an API key
)

# Render map (st.pydeck_chart supports click selections in modern Streamlit)
event = st.pydeck_chart(r, on_select="rerun", selection_mode="single-object", height=500)

selected_gmap_id = None

# Extract selected gmap_id if a user clicks a point
if event and hasattr(event, "selection"):
    # Streamlit returning PydeckSelectionState has .selection.objects that maps layer ID -> list of row dicts
    objects_dict = getattr(event.selection, "objects", {})
    if not objects_dict and isinstance(event.selection, dict):
        objects_dict = event.selection.get("objects", {})
        
    restaurants_sel = objects_dict.get("restaurants", [])
    if restaurants_sel:
        # Some versions wrap the dict inside an "object" key, some provide the dict directly
        first_selection = restaurants_sel[0]
        if "object" in first_selection and isinstance(first_selection["object"], dict):
            selected_gmap_id = first_selection["object"].get("gmap_id")
        else:
            selected_gmap_id = first_selection.get("gmap_id")

st.divider()

# Display Reviews
if selected_gmap_id:
    # Get restaurant details
    rest_info = df_meta[df_meta['gmap_id'] == selected_gmap_id].iloc[0]
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header(f"Reviews for {rest_info['name']}")
    with col2:
        if pd.notna(rest_info.get('url')):
            st.link_button("View on Google Maps 🗺️", rest_info['url'])
            
    reviews = get_restaurant_reviews(selected_gmap_id)
    
    if len(reviews) == 0:
        st.info("No reviews found for this restaurant.")
    else:
        st.caption(f"Found {len(reviews)} reviews")
        
        # Sort reviews by time descending if time exists
        if 'time' in reviews.columns:
            reviews = reviews.sort_values(by='time', ascending=False)
            
        for _, row in reviews.iterrows():
            with st.container(border=True):
                # Review Header: Name and Rating
                reviewer_name = row['name'] if pd.notna(row['name']) else "Anonymous"
                rating = float(row['rating']) if pd.notna(row['rating']) else 0.0
                st.subheader(f"👤 {reviewer_name} | {'⭐' * int(rating)}")
                
                # Timestamp
                if pd.notna(row.get('time')):
                    try:
                        # Assuming time is in milliseconds epoch
                        time_obj = datetime.datetime.fromtimestamp(row['time'] / 1000.0)
                        st.caption(f"🕒 {time_obj.strftime('%Y-%m-%d %H:%M')}")
                    except:
                        pass
                
                # Review Text
                text = row['text'] if pd.notna(row['text']) else ""
                if text.strip():
                    st.write(text)
                
                # Images
                pics = row.get('pics')
                
                # Safely check if pics is valid (not None or NaN)
                valid_pics = False
                if pics is not None:
                    if isinstance(pics, float) and pd.isna(pics):
                        pass
                    else:
                        valid_pics = True

                if valid_pics:
                    try:
                        # PyArrow parses nested arrays as numpy arrays or lists
                        # Assuming the schema is: list of dicts with 'url' containing lists of strings
                        if hasattr(pics, '__iter__'):
                            img_urls = []
                            for pic in pics:
                                if isinstance(pic, dict) and 'url' in pic:
                                    urls = pic['url']
                                    if hasattr(urls, '__iter__') and len(urls) > 0:
                                        img_urls.append(urls[0])
                            
                            if img_urls:
                                st.image(img_urls, width=150)
                    except Exception as e:
                        print(f"Failed to parse images: {e}")
                        
else:
    st.info("👆 Click on any restaurant marker on the map above to load its reviews here.")
