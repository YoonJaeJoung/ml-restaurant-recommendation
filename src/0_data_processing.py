"""
data_processing.py
Data loading, cleaning, and preprocessing utilities.
"""

import gzip
import json
import os
from pathlib import Path

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

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def _open_file(file_path):
    """
    自动打开 .json 或 .json.gz 文件
    """
    if file_path.endswith('.gz'):
        return gzip.open(file_path, 'rt', encoding='utf-8')
    else:
        return open(file_path, 'r', encoding='utf-8')

def process_restaurant_data(
    meta_input_path: str,
    meta_output_path: str,
    reviews_input_path: str,
    reviews_output_path: str
):
    """
    Reads raw Google Local Reviews metadata, filters for valid restaurants in NYC boroughs,
    and writes out a processed Parquet file.
    Then, reads the review data, filters for only reviews belonging to those restaurants,
    and streams them to a processed Parquet file.
    """
    os.makedirs(os.path.dirname(meta_output_path), exist_ok=True)
    
    # ---------------------------------------------------------
    # 1. Process Metadata
    # ---------------------------------------------------------
    print("Processing Metadata...")
    meta_records = []
    with gzip.open(meta_input_path, 'rt', encoding='utf-8') as f_in:
        for line in f_in:
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
                
            # Filter 3: Determine borough
            parts = address.split(", ")
            if len(parts) >= 2:
                neighborhood = parts[-2]
                borough = BOROUGH_MAP.get(neighborhood)
            else:
                borough = None
                
            if borough in VALID_BOROUGHS:
                row['borough'] = borough
                meta_records.append(row)

    # Convert to DataFrame and save as Parquet
    df_meta = pd.DataFrame(meta_records)
    df_meta.to_parquet(meta_output_path, engine='pyarrow', index=False)
    print(f"Saved {len(df_meta)} metadata records to {meta_output_path}")

    # ---------------------------------------------------------
    # 2. Process Reviews
    # ---------------------------------------------------------
    print("Processing Reviews...")
    valid_gmap_ids = set(df_meta['gmap_id'].dropna())
    
    chunk_size = 100000
    chunk = []
    writer = None
    
    with gzip.open(reviews_input_path, 'rt', encoding='utf-8') as f_in:
        for line in f_in:
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
                    writer = pq.ParquetWriter(reviews_output_path, table.schema)
                    
                writer.write_table(table)
                chunk = []
                
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
        
    print(f"Finished processing and saving reviews to {reviews_output_path}")

if __name__ == "__main__":
    process_restaurant_data(
        meta_input_path="data/raw/meta-New_York.json.gz",
        meta_output_path="data/processed/meta-NYC-restaurant.parquet",
        reviews_input_path="data/raw/review-New_York.json.gz",
        reviews_output_path="data/processed/review-NYC-restaurant.parquet"
    )
