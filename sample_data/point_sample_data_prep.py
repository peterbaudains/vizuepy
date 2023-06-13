import xml.etree.ElementTree as ET
import pandas as pd
import geopandas as gpd
import datetime as dt
from urllib.request import urlopen

"""
Sample data is obtained from the UK Food Standards Agency Food Hyegience Rating Data API, available from: https://ratings.food.gov.uk/open-data/
Data is made avialable under the Open Government License (OGL) v3: https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
"""

city_of_london_data_url = "https://ratings.food.gov.uk/OpenDataFiles/FHRS508en-GB.xml"

# Read and format xml data
with urlopen(city_of_london_data_url) as f:
    df = pd.read_xml(f, 
                     parser='etree', 
                     iterparse={"EstablishmentDetail": ["FHRSID", "BusinessType", "RatingValue", "RatingDate", "LocalAuthorityName"]})
    
with urlopen(city_of_london_data_url) as f:
    df_scores = pd.read_xml(f, parser='etree', iterparse={"Scores":["Hygiene", "Structural", "ConfidenceInManagement"]})

with urlopen(city_of_london_data_url) as f:
    df_geocode = pd.read_xml(f, parser='etree', iterparse={"Geocode": ["Longitude", "Latitude"]})

df = df.merge(df_scores, left_index=True, right_index=True)
df = df.merge(df_geocode, left_index=True, right_index=True)

# Filter df to only include records with a geocode
df = df[(~df['Latitude'].isna()) & (~df['Longitude'].isna())]

# Add Eastings and Northings columns using a geopandas transformation
df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['Longitude'], df['Latitude']), crs=4326)
df = df.to_crs(27700)
df['Easting'] = df['geometry'].apply(lambda p: p.x)
df['Northing'] = df['geometry'].apply(lambda p: p.y)


# Save file
df[['FHRSID','BusinessType','RatingValue','RatingDate','LocalAuthorityName','Hygiene','Structural','ConfidenceInManagement','Longitude','Latitude','Easting','Northing']]\
    .to_csv('FoodHygeineRatings_CityOfLondon_accessed%s.csv' % dt.datetime.now().strftime(format='%Y%m%d'), index=False)