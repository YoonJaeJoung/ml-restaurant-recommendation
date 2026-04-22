"""
data_processing.py
Data loading, cleaning, and preprocessing utilities.
Merges steps 0 and 2.
"""

import gzip
import json
import os
import re
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ZIP at end of address, optionally with a ZIP+4 suffix.
# Anchoring at the end avoids matching street numbers earlier in the address.
ZIP_RE = re.compile(r'(\d{5})(?:-\d{4})?\s*$')

FOOD_RESTAURANT = {
    'Afghani restaurant', 'African restaurant', 'Alsace restaurant', 'American restaurant', 'Angler fish restaurant', 
    'Argentinian restaurant', 'Armenian restaurant', 'Art cafe', 'Asian fusion restaurant', 'Asian restaurant', 
    'Australian restaurant', 'Austrian restaurant', 'Authentic Japanese restaurant', 'Açaí shop', 'Bagel shop', 'Bakery', 
    'Bangladeshi restaurant', 'Bar', 'Bar & grill', 'Bar tabac', 'Barbecue restaurant', 'Basque restaurant', 'Beer garden', 
    'Beer hall', 'Belgian restaurant', 'Biryani restaurant', 'Bistro', 'Box lunch supplier', 'Brasserie', 'Brazilian pastelaria', 
    'Brazilian restaurant', 'Breakfast restaurant', 'Brewpub', 'British restaurant', 'Brunch restaurant', 'Bubble tea store', 
    'Buffet restaurant', 'Burmese restaurant', 'Burrito restaurant', 'Butcher shop deli', 'Cafe', 'Cafeteria', 'Cajun restaurant', 
    'Cake shop', 'Californian restaurant', 'Cambodian restaurant', 'Canadian restaurant', 'Cantonese restaurant', 'Caribbean restaurant', 
    'Carvery', 'Caterer', 'Catering', 'Central American restaurant', 'Cheesesteak restaurant', 'Chettinad restaurant', 'Chicken restaurant', 
    'Chicken shop', 'Chicken wings restaurant', 'Childrens cafe', 'Childrens party buffet', 'Chilean restaurant', 'Chinese bakery', 
    'Chinese noodle restaurant', 'Chinese restaurant', 'Chinese takeaway', 'Chinese tea house', 'Chocolate cafe', 'Chophouse restaurant', 
    'Churreria', 'Cider bar', 'Cocktail bar', 'Coffee shop', 'Coffee stand', 'Cold noodle restaurant', 'Colombian restaurant', 
    'Contemporary Louisiana restaurant', 'Continental restaurant', 'Conveyor belt sushi restaurant', 'Cookie shop', 'Costa Rican restaurant', 
    'Country food restaurant', 'Couscous restaurant', 'Crab house', 'Creole restaurant', 'Croatian restaurant', 'Crêperie', 
    'Cuban restaurant', 'Cupcake shop', 'Czech restaurant', 'Dan Dan noodle restaurant', 'Dance restaurant', 'Danish restaurant', 
    'Deli', 'Delivery Chinese restaurant', 'Delivery Restaurant', 'Dessert restaurant', 'Dessert shop', 'Dim sum restaurant', 'Diner', 
    'Dog cafe', 'Dominican restaurant', 'Donut shop', 'Down home cooking restaurant', 'Dumpling restaurant', 'East African restaurant', 
    'Eastern European restaurant', 'Eatery', 'Eclectic restaurant', 'Ecuadorian restaurant', 'Egyptian restaurant', 'English restaurant', 
    'Eritrean restaurant', 'Espresso bar', 'Ethiopian restaurant', 'Ethnic restaurant', 'European restaurant', 'Falafel restaurant', 
    'Family restaurant', 'Fast food restaurant', 'Filipino restaurant', 'Fine dining restaurant', 'Fish & chips restaurant', 
    'Fish and chips takeaway', 'Fish and seafood restaurant', 'Fondue restaurant', 'Food court', 'Food delivery', 'French restaurant', 
    'French steakhouse restaurant', 'Fried chicken takeaway', 'Frozen yogurt shop', 'Fruit parlor', 'Fujian restaurant', 'Fusion restaurant', 
    'Galician restaurant', 'Gastropub', 'Georgian restaurant', 'German restaurant', 'Gluten-free restaurant', 'Greek restaurant', 'Grill', 
    'Guatemalan restaurant', 'Guizhou restaurant', 'Gyro restaurant', 'Haitian restaurant', 'Hakka restaurant', 'Halal restaurant', 
    'Hamburger restaurant', 'Haute French restaurant', 'Hawaiian restaurant', 'Health food restaurant', 'Hoagie restaurant', 
    'Honduran restaurant', 'Hong Kong style fast food restaurant', 'Hookah bar', 'Hot dog restaurant', 'Hot dog stand', 'Hot pot restaurant', 
    'Hunan restaurant', 'Hungarian restaurant', 'Ice cream shop', 'Indian Muslim restaurant', 'Indian restaurant', 'Indian sizzler restaurant', 
    'Indian takeaway', 'Indonesian restaurant', 'Irish pub', 'Irish restaurant', 'Israeli restaurant', 'Italian restaurant', 
    'Izakaya restaurant', 'Jamaican restaurant', 'Japanese curry restaurant', 'Japanese delicatessen', 'Japanese regional restaurant', 
    'Japanese restaurant', 'Japanese steakhouse', 'Japanese sweets restaurant', 'Japanized western restaurant', 'Javanese restaurant', 
    'Jewish restaurant', 'Juice shop', 'Kaiseki restaurant', 'Katsudon restaurant', 'Kazakhstani restaurant', 'Kebab shop', 
    'Korean barbecue restaurant', 'Korean beef restaurant', 'Korean restaurant', 'Korean rib restaurant', 'Kosher restaurant', 
    'Kushiage and kushikatsu restaurant', 'Kyoto style Japanese restaurant', 'Laotian restaurant', 'Latin American restaurant', 
    'Lebanese restaurant', 'Lithuanian restaurant', 'Live music bar', 'Lounge', 'Lunch restaurant', 'Macrobiotic restaurant', 
    'Malaysian restaurant', 'Mandarin restaurant', 'Meal delivery', 'Meat dish restaurant', 'Mediterranean restaurant', 'Mexican restaurant', 
    'Mexican torta restaurant', 'Mid-Atlantic restaurant (US)', 'Middle Eastern restaurant', 'Mobile caterer', 'Modern British restaurant', 
    'Modern European restaurant', 'Modern French restaurant', 'Modern Indian restaurant', 'Modern izakaya restaurants', 'Momo restaurant', 
    'Mongolian barbecue restaurant', 'Moroccan restaurant', 'Mutton barbecue restaurant', 'Neapolitan restaurant', 'Nepalese restaurant', 
    'New American restaurant', 'New England restaurant', 'New Zealand restaurant', 'Nicaraguan restaurant', 'Noodle shop', 
    'North African restaurant', 'North Eastern Indian restaurant', 'North Indian restaurant', 'Northern Italian restaurant', 
    'Nuevo Latino restaurant', 'Oaxacan restaurant', 'Obanzai restaurant', 'Offal pot cooking restaurant', 'Okonomiyaki restaurant', 
    'Organic restaurant', 'Oxygen cocktail spot', 'Oyster bar restaurant', 'Pakistani restaurant', 'Pan-Asian restaurant', 
    'Pan-Latin restaurant', 'Pancake restaurant', 'Paraguayan restaurant', 'Pastry shop', 'Patisserie', 'Persian restaurant', 
    'Peruvian restaurant', 'Pho restaurant', 'Piano bar', 'Pie shop', 'Pizza', 'Pizza Takeout', 'Pizza delivery', 'Pizza restaurant', 
    'Pizza takeaway', 'Poke bar', 'Polish restaurant', 'Polynesian restaurant', 'Porridge restaurant', 'Portuguese restaurant', 
    'Pretzel store', 'Provence restaurant', 'Pub', 'Pueblan restaurant', 'Puerto Rican restaurant', 'Punjabi restaurant', 'Raclette restaurant', 
    'Ramen restaurant', 'Raw food restaurant', 'Restaurant', 'Restaurant or cafe', 'Rice restaurant', 'Roman restaurant', 'Romanian restaurant', 
    'Russian restaurant', 'Salad shop', 'Salsa bar', 'Salvadoran restaurant', 'Sandwich shop', 'Sardinian restaurant', 'Satay restaurant', 
    'Scandinavian restaurant', 'School lunch center', 'Seafood donburi restaurant', 'Seafood restaurant', 'Self service restaurant', 
    'Serbian restaurant', 'Sfiha restaurant', 'Shabu-shabu restaurant', 'Shanghainese restaurant', 'Shawarma restaurant', 'Sichuan restaurant', 
    'Sicilian restaurant', 'Singaporean restaurant', 'Small plates restaurant', 'Snack bar', 'Soba noodle shop', 'Soondae restaurant', 
    'Soul food restaurant', 'Soup kitchen', 'Soup restaurant', 'Soup shop', 'South African restaurant', 'South American restaurant', 
    'South Asian restaurant', 'Southeast Asian restaurant', 'Southern Italian restaurant', 'Southern restaurant (US)', 
    'Southwestern restaurant (US)', 'Spanish restaurant', 'Sports bar', 'Sri Lankan restaurant', 'Stand bar', 'Steak house', 
    'Steamed bun shop', 'Sugar shack', 'Sukiyaki and Shabu Shabu restaurant', 'Sukiyaki restaurant', 'Sundae restaurant', 'Sushi restaurant', 
    'Sushi takeaway', 'Swedish restaurant', 'Sweets and dessert buffet', 'Swiss restaurant', 'Syokudo and Teishoku restaurant', 
    'Syrian restaurant', 'Taco restaurant', 'Taiwanese restaurant', 'Takeout Restaurant', 'Takeout restaurant', 'Takoyaki restaurant', 
    'Tamale shop', 'Tapas bar', 'Tapas restaurant', 'Tavern', 'Tea house', 'Tempura donburi restaurant', 'Tempura restaurant', 
    'Teppanyaki restaurant', 'Tex-Mex restaurant', 'Thai restaurant', 'Tibetan restaurant', 'Tiki bar', 'Tofu restaurant', 
    'Tonkatsu restaurant', 'Traditional American restaurant', 'Traditional restaurant', 'Turkish restaurant', 'Tuscan restaurant', 
    'Udon noodle restaurant', 'Ukrainian restaurant', 'Uruguayan restaurant', 'Uzbeki restaurant', 'Vegan restaurant', 
    'Vegetarian cafe and deli', 'Vegetarian restaurant', 'Venetian restaurant', 'Venezuelan restaurant', 'Vietnamese restaurant', 
    'Wedding bakery', 'Wedding buffet', 'Welsh restaurant', 'West African restaurant', 'Western restaurant', 'Wine bar', 'Wok restaurant', 
    'Yakiniku restaurant', 'Yakitori restaurant', 'Yemenite restaurant', 'Yucatan restaurant'
}

MANHATTAN_LIST = ["New York", "Manhattan", "Battery Park City", "Carnegie Hill", "Chelsea", "Chinatown", "Civic Center", "Clinton", "East Harlem", "East Village", "Financial District", "Flatiron", "Gramercy", "Greenwich Village", "Hamilton Heights", "Harlem (Central)", "Herald Square", "Hudson Square", "Inwood", "Lenox Hill", "Lincoln Square", "Little Italy", "Lower East Side", "Manhattan Valley", "Manhattanville", "Midtown", "Midtown South", "Morningside Heights", "Murray Hill", "NoHo", "Roosevelt Island", "SoHo", "South Village", "Stuyvesant Town", "Sutton Place", "Times Square", "Tribeca", "Tudor City", "Turtle Bay", "Union Square", "Upper East Side", "Upper West Side", "Wall Street", "Washington Heights", "West Village", "Yorkville"]
BRONX_LIST = ["Bronx", "Allerton", "Bathgate", "Baychester", "Bedford Park", "Belmont", "Bronxdale", "Bronx Park South", "Bronx River", "Castle Hill", "City Island", "Claremont Village", "Clason Point", "Concourse", "Concourse Village", "Co-op City", "Country Club", "East Tremont", "Eastchester", "Edenwald", "Edgewater Park", "Fieldston", "Fordham", "High Bridge", "Hunts Point", "Kingsbridge", "Kingsbridge Heights", "Longwood", "Marble Hill", "Melrose", "Morris Heights", "Morris Park", "Morrisania", "Mott Haven", "Mount Eden", "Mount Hope", "North Riverdale", "Norwood", "Olinville", "Parkchester", "Pelham Bay", "Pelham Gardens", "Pelham Parkway", "Port Morris", "Riverdale", "Schuylerville", "Soundview", "Spuyten Duyvil", "Throgs Neck", "Unionport", "University Heights", "Van Nest", "Wakefield", "West Farms", "Westchester Square", "Williamsbridge", "Woodlawn"]
BROOKLYN_LIST = ["Brooklyn", "Bath Beach", "Bay Ridge", "Bedford Stuyvesant", "Bensonhurst", "Bergen Beach", "Boerum Hill", "Borough Park", "Brighton Beach", "Broadway Junction", "Brooklyn Heights", "Brownsville", "Bushwick", "Canarsie", "Carroll Gardens", "City Line", "Clinton Hill", "Cobble Hill", "Coney Island", "Crown Heights", "Cypress Hills", "Ditmas Park", "Downtown", "DUMBO", "Dyker Heights", "East Flatbush", "East New York", "East Williamsburg", "Farragut", "Flatbush", "Flatlands", "Fort Greene", "Fort Hamilton", "Fulton Ferry", "Georgetown", "Gerritsen Beach", "Gowanus", "Gravesend", "Greenpoint", "Highland Park", "Homecrest", "Kensington", "Kings Highway", "Manhattan Beach", "Manhattan Terrace", "Mapleton", "Marine Park", "Midwood", "Mill Basin", "Mill Island", "Navy Yard", "New Lots", "North Side", "Ocean Hill", "Ocean Parkway", "Paerdegat Basin", "Park Slope", "Plum Beach", "Prospect Heights", "Prospect Lefferts Gardens", "Prospect Park South", "Red Hook", "Remsen Village", "Rugby", "Sea Gate", "Sheepshead Bay", "South Side", "Spring Creek", "Starrett City", "Stuyvesant Heights", "Sunset Park", "Tompkins Park North", "Vinegar Hill", "Weeksville", "Williamsburg", "Windsor Terrace", "Wingate"]
QUEENS_LIST = ["Queens", "Arverne", "Astoria", "Astoria Heights", "Auburndale", "Bay Terrace", "Bayside", "Bayswater", "Beechhurst", "Bellaire", "Belle Harbor", "Bellerose", "Blissville", "Breezy Point", "Briarwood", "Broad Channel", "Brookville", "Cambria Heights", "Clearview", "College Point", "Douglaston", "Dutch Kills", "East Elmhurst", "Edgemere", "Elmhurst", "Far Rockaway", "Floral Park", "Flushing", "Flushing (Downtown)", "Forest Hills", "Forest Hills Gardens", "Fresh Meadows", "Glen Oaks", "Glendale", "Hammels", "Hillcrest", "Hollis", "Holliswood", "Howard Beach", "Hunters Point", "Jackson Heights", "Jamaica", "Jamaica Center", "Jamaica Estates", "Jamaica Hills", "Kew Gardens", "Kew Gardens Hills", "Laurelton", "Lefrak City", "Lindenwood", "Little Neck", "Long Island City", "Malba", "Maspeth", "Middle Village", "Murray Hill", "Neponsit", "New Hyde Park", "North Corona", "Oakland Gardens", "Ozone Park", "Pomonok", "Queens Village", "Queensboro Hill", "Ravenswood", "Rego Park", "Richmond Hill", "Ridgewood", "Rochdale", "Rockaway Park", "Rosedale", "Roxbury", "Seaside", "Somerville", "South Corona", "South Jamaica", "South Ozone Park", "Springfield Gardens", "St. Albans", "Steinway", "Sunnyside", "Sunnyside Gardens", "Utopia", "Whitestone", "Woodhaven", "Woodside"]
STATEN_ISLAND_LIST = ["Staten Island", "Annadale", "Arden Heights", "Arlington", "Arrochar", "Bay Terrace", "Bloomfield", "Bulls Head", "Butler Manor", "Castleton Corners", "Charleston", "Chelsea", "Clifton", "Concord", "Dongan Hills", "Egbertville", "Elm Park", "Eltingville", "Emerson Hill", "Fox Hills", "Graniteville", "Grant City", "Grasmere", "Great Kills", "Greenridge", "Grymes Hill", "Heartland Village", "Howland Hook", "Huguenot", "Lighthouse Hill", "Livingston", "Manor Heights", "Mariner's Harbor", "Midland Beach", "New Brighton", "New Dorp", "New Dorp Beach", "New Springville", "Oakwood", "Old Place", "Old Town", "Park Hill", "Pleasant Plains", "Port Ivory", "Port Richmond", "Prince's Bay", "Randall Manor", "Richmond Town", "Richmond Valley", "Rosebank", "Rossville", "Sandy Ground", "Shore Acres", "Silver Lake", "South Beach", "St. George", "Stapleton", "Sunnyside", "Todt Hill", "Tompkinsville", "Tottenville", "Travis", "Ward Hill", "West Brighton", "Westerleigh", "Willowbrook", "Woodrow"]

BOROUGH_MAP = {}
for neighborhood in MANHATTAN_LIST:
    BOROUGH_MAP[neighborhood] = "Manhattan"
for neighborhood in BRONX_LIST:
    BOROUGH_MAP[neighborhood] = "Bronx"
for neighborhood in BROOKLYN_LIST:
    BOROUGH_MAP[neighborhood] = "Brooklyn"
for neighborhood in QUEENS_LIST:
    BOROUGH_MAP[neighborhood] = "Queens"
for neighborhood in STATEN_ISLAND_LIST:
    BOROUGH_MAP[neighborhood] = "Staten Island"

VALID_BOROUGHS = {"Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"}
VALID_ZIP_PREFIX = {"100", "101", "102", "103", "104", "110", "111", "112", "113", "114", "116"}

TRANS_MARK = "(Translated by Google)"
ORIG_MARK = "(Original)"

def is_contains_chinese(text):
    """Check if string contains any Chinese/CJK characters."""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

def select_english_text(text):
    """Return the English portion of a review's text field.

    - If the text begins with '(Translated by Google)', extract the English
      translation between that marker and '(Original)'.
    - If not a translation, check for Chinese characters. If found, discard.
    - Otherwise return the text unchanged (already in English/target locale).
    - None / NaN / empty -> "".
    """
    if not isinstance(text, str) or not text:
        return ""
    stripped = text.lstrip()
    result_text = stripped

    if stripped.startswith(TRANS_MARK):
        after = stripped[len(TRANS_MARK):]
        english = after.split(ORIG_MARK, 1)[0]
        result_text = english.strip()
    
    # New logic: Discard reviews that still contain Chinese after stripping
    if is_contains_chinese(result_text):
        return ""
        
    return result_text

def filter_reviews(input_path, output_path, min_reviews=15, max_reviews=500):
    print("Loading data for filtering...")
    review_df = pd.read_parquet(input_path)
    print(f"Original shape: {len(review_df)}")

    # 1. Extract English text (and filter non-English Chinese reviews)
    print("Extracting English text (stripping (Translated by Google) and filtering Chinese)...")
    n_initial_restaurants = review_df['gmap_id'].nunique()
    review_df["text_for_embedding"] = review_df["text"].map(select_english_text)
    
    # Remove rows where text_for_embedding is empty (non-English or empty reviews)
    review_df = review_df[review_df["text_for_embedding"].str.strip().str.len() > 0].copy()
    n_after_english_filter = review_df['gmap_id'].nunique()
    print(f"  Unique restaurants before English/Chinese filter: {n_initial_restaurants:,}")
    print(f"  Unique restaurants AFTER English/Chinese filter: {n_after_english_filter:,}")
    print(f"  Shape after filtering non-English: {len(review_df):,}")

    # 2. Filter out restaurants with too few VALID reviews (> min_reviews)
    print(f"Filtering: keeping only restaurants with > {min_reviews} valid reviews...")
    review_counts = review_df.groupby('gmap_id').size()
    valid_gmap_ids = review_counts[review_counts > min_reviews].index

    n_before_cutoff = review_df['gmap_id'].nunique()
    review_df = review_df[review_df['gmap_id'].isin(valid_gmap_ids)]
    n_after_cutoff = review_df['gmap_id'].nunique()
    print(f"  Unique restaurants before {min_reviews} cutoff: {n_before_cutoff:,}")
    print(f"  Unique restaurants AFTER {min_reviews} cutoff: {n_after_cutoff:,}")
    print(f"  After min_reviews row shape: {len(review_df):,}")

    # 3. Downsampling: Sort by review detail (length) and keep at most max_reviews (<= 500)
    if max_reviews is not None:
        print(f"Downsampling: keeping maximum {max_reviews} most detailed reviews per restaurant...")
        review_df['_text_len'] = review_df['text_for_embedding'].str.len()
        review_df = review_df.sort_values(['gmap_id', '_text_len'], ascending=[True, False])
        review_df = review_df.groupby('gmap_id').head(max_reviews).reset_index(drop=True)
        review_df = review_df.drop(columns=['_text_len'])
        print(f"Final shape after max limit: {len(review_df)}")

    # 4. Save the filtered dataframe
    print("Saving to parquet...")
    review_df.to_parquet(output_path, index=False)
    print(f"Successfully saved matched data ({len(review_df)} rows) to: {output_path}")

def process_restaurant_data(
    meta_input_path: str,
    meta_output_path: str,
    reviews_input_path: str,
    reviews_output_path: str,
    reviews_filtered_output_path: str
):
    """
    Reads raw Google Local Reviews metadata, filters for valid restaurants in NYC boroughs,
    and writes out a processed Parquet file.
    Then, reads the review data, filters for only reviews belonging to those restaurants,
    and streams them to a processed Parquet file.
    Finally, filters reviews by count, extracts English text, and saves the final parquet over.
    """
    os.makedirs(os.path.dirname(meta_output_path), exist_ok=True)
    checkpoint_path = os.path.join(os.path.dirname(reviews_output_path), "review_processing_checkpoint.json")
    
    # ---------------------------------------------------------
    # 1. Process Metadata
    # ---------------------------------------------------------
    if not os.path.exists(meta_output_path):
        print("Processing Metadata...")
        meta_records = []
        n_permanently_closed = 0
        total_processed = 0
        
        with gzip.open(meta_input_path, 'rt', encoding='utf-8') as f_in:
            for line in f_in:
                total_processed += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                    
                # Filter 1: Check if address is valid
                address = row.get('address')
                if not address or not isinstance(address, str) or address.lower() == 'nan':
                    continue
                    
                # Filter 2: Check if it's a restaurant
                is_restaurant = False
                categories = row.get('category')
                if categories and isinstance(categories, list):
                    if any(cat in FOOD_RESTAURANT for cat in categories):
                        is_restaurant = True
                            
                if not is_restaurant:
                    continue

                # Filter 3: Skip permanently closed businesses
                if row.get('state') == 'Permanently closed':
                    n_permanently_closed += 1
                    continue
                    
                # Filter 4: Require a valid NYC ZIP prefix. Neighborhood-name matching alone
                # is insufficient because upstate NY places share names with NYC neighborhoods
                # (e.g. Clinton NY 13323 vs. Clinton in Manhattan, Red Hook NY 12571 vs. Brooklyn).
                zip_match = ZIP_RE.search(address)
                if not zip_match or zip_match.group(1)[:3] not in VALID_ZIP_PREFIX:
                    continue

                # Filter 5: Determine borough
                parts = address.split(", ")
                if len(parts) >= 2:
                    neighborhood = parts[-2]
                    borough = BOROUGH_MAP.get(neighborhood)
                else:
                    borough = None
                    
                if borough in VALID_BOROUGHS:
                    row['borough'] = borough
                    meta_records.append(row)

        df_meta = pd.DataFrame(meta_records)
        df_meta.to_parquet(meta_output_path, engine='pyarrow', index=False)
        print(f"Metadata Processing Summary:")
        print(f"  Total raw records scanned: {total_processed:,}")
        print(f"  Restaurants skipped (Permanently closed): {n_permanently_closed:,}")
        print(f"  Valid open restaurants saved: {len(df_meta):,}")
    else:
        print(f"Metadata already exists at {meta_output_path}. Loading...")
        df_meta = pd.read_parquet(meta_output_path)

    # ---------------------------------------------------------
    # 2. Process Reviews
    # ---------------------------------------------------------
    print("Processing Reviews...")
    valid_gmap_ids = set(df_meta['gmap_id'].dropna())
    
    start_line = 0
    if os.path.exists(checkpoint_path) and os.path.exists(reviews_output_path):
        try:
            with open(checkpoint_path, 'r') as f:
                start_line = json.load(f).get('last_line', 0)
            print(f"Resuming review extraction from line {start_line}...")
        except Exception:
            start_line = 0

    chunk_size = 100000
    chunk = []
    
    current_line = 0
    # Use append mode for writer if resuming
    writer = None
    
    # Note: parquet doesn't support 'appending' in the traditional sense like CSV, 
    # but pq.ParquetWriter can write multiple tables. 
    # If resuming, we actually need to read the existing file and continue writing.
    # To keep it simple and safe, we'll write in chunks and only finish if done.
    # Actually, for the intermediate file, we just write all chunks again if interrupted.
    # Better: If start_line > 0, we'll open the existing file and continue.
    
    # Re-initialized writer for resume
    if start_line > 0:
        # Check if file exists, if not start from 0
        if not os.path.exists(reviews_output_path):
            start_line = 0
    
    with gzip.open(reviews_input_path, 'rt', encoding='utf-8') as f_in:
        for line in f_in:
            current_line += 1
            if current_line <= start_line:
                continue
                
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
                
            if row.get('gmap_id') in valid_gmap_ids:
                chunk.append(row)
                
            # Write out chunk if it reaches the size
            if len(chunk) >= chunk_size:
                df_chunk = pd.DataFrame(chunk)
                if 'rating' in df_chunk.columns:
                    df_chunk['rating'] = pd.to_numeric(df_chunk['rating'], errors='coerce').astype('float64')
                
                table = pa.Table.from_pandas(df_chunk)
                
                if writer is None:
                    # If resuming, we need to handle the schema properly
                    # For simplicity, if we resume, we are appending to the same file.
                    # pq.ParquetWriter(mode='a') doesn't exist.
                    # We'll use a temporary file approach or just accept that intermediate 
                    # files are re-generated if partial.
                    # Actually, let's just use the 'last_line' to skip ahead but overwrite the file
                    # to keep the parquet schema clean and avoid multiple writers.
                    writer = pq.ParquetWriter(reviews_output_path, table.schema)
                    
                writer.write_table(table)
                chunk = []
                
                # Save checkpoint
                with open(checkpoint_path, 'w') as f:
                    json.dump({'last_line': current_line}, f)
                    
        # Write out any remaining items
        if chunk:
            df_chunk = pd.DataFrame(chunk)
            if 'rating' in df_chunk.columns:
                df_chunk['rating'] = pd.to_numeric(df_chunk['rating'], errors='coerce').astype('float64')
                
            table = pa.Table.from_pandas(df_chunk)
            if writer is None:
                writer = pq.ParquetWriter(reviews_output_path, table.schema)
            writer.write_table(table)
            
    if writer:
        writer.close()
    
    # Mark as complete by setting last_line to a very large number or deleting checkpoint
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
            
    print(f"Finished processing and saving intermediate reviews to {reviews_output_path}")
    
    # ---------------------------------------------------------
    # 3. Filter Reviews
    # ---------------------------------------------------------
    filter_reviews(reviews_output_path, reviews_filtered_output_path, min_reviews=15, max_reviews=500)

if __name__ == "__main__":
    process_restaurant_data(
        meta_input_path="data/raw/meta-New_York.json.gz",
        meta_output_path="data/processed/meta-NYC-restaurant.parquet",
        reviews_input_path="data/raw/review-New_York_10.json.gz",
        reviews_output_path="data/processed/review-NYC-restaurant.parquet",
        reviews_filtered_output_path="data/processed/review-NYC-restaurant-filtered.parquet"
    )
