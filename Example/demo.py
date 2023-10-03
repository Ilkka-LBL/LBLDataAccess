# -*- coding: utf-8 -*-
"""
Created on Tue Feb  7 09:07:41 2023

@author: ISipila

Problem setting: we want to map the change in the percentage of population with very good health in the census from 2011 to 2022 at ward 
level for Lewisham and surrounding councils

Why this is difficult? 
    - Ward boundaries have changed 
    - Many different councils involved
    - Not all census tables are available at all geographic levels. For instance health data is only available at OA level for 2011 Census

To install LBLDataAccess:
    python -m pip install git+https://github.com/lb-lewisham/LBLDataAccess.git

"""
#%%
from LBLDataAccess.load_geocodes import GeoHelper, SmartGeocodeLookup
from LBLDataAccess.access_nomis import DownloadFromNomis
from pathlib import Path
import json 
import pandas as pd

pd.set_option('display.max_columns', None)

# load NOMIS api key and proxies from settings.txt
settings = Path('settings.txt')
with open(settings, 'r') as f:
    settings = json.load(f)
    
nomis_api = settings['nomis_api_key']
proxies = settings['proxies']  # ignore this when using on Google Colab or outside organisational proxy

#%%
#print(proxies)
from LBLDataAccess.load_geocodes import SmartGeocodeLookup
gss = SmartGeocodeLookup(starting_column='WD22CD', ending_column='LSOA21CD', local_authorities=['Lewisham'])

geocodes = gss.get_filtered_geocodes()
#%%
geocodes
#%% We want to have a look at what data we want from NOMIS. We do that by making an api call to nomis and open a connection:
    
conn = DownloadFromNomis(api_key=nomis_api, proxies=proxies, memorize=True)  
# we set the memorize to True so we don't have to always read the settings file when using this class
conn.connect()

#%% Now that we have a connection, let's see what's available to us:
conn.print_table_info()

#%% We can see literally hundreds of tables. In addition to Census data, there's also JSA and other employment data. Some data
# are constantly updated and new tables are added. 

# Okay, but we still need to know what tables we can use. So let's choose a variable, in this case General Health, which is table NM_2055_1
# for 2021 census and NM_1546_1 for 2011 census. We can get more information about them:
    
conn.detailed_info_for_table('NM_2055_1')
conn.detailed_info_for_table('NM_1546_1') 

# So, looking at the Metadata for the two tables, we can already see that neither table has ward level information available, so we have to 
# manually create our ward level data.

#%% We now have the option of downloading the tables as bulk or we can just download the rows for our desired geographic areas. 
# Let's do bulk download first:
    
health_2021_bulk = conn.get_bulk('NM_2055_1')
health_2011_bulk = conn.get_bulk('NM_1546_1')

#%% The problem with the above is that not all tables are available as bulk and these are large files with 100,000+ rows, 
# which means that the download takes a long time:
print(len(health_2021_bulk), len(health_2011_bulk))

# We can now start filtering this bulk data using the geocodes, which we will be doing next.

#%% So, let's be smarter and only download the relevant NOMIS data at OA level for 2011 and 2021 censuses. 
# To do that, we need the appropriate GSS codes. We have two main helper functions that can help us decipher the geocode hell:
    
GeoHelper().geography_keys()  # short hand descriptions of the letters before the years. 

GeoHelper().available_geographies()  # all codes that we can use in our selection

#%% To get the list of folder names that we can use:
print(GeoHelper().year_options) 
#%% And then we pick 2011 to have a look at available geographies:
GeoHelper().available_geographies('2011')

# Using these tools can help you choose your right geocodes, but are not necessary once you roughly know what geographic areas there are.

#%% Once you know the codes you want, and we want OA21CD and OA11CD for downloading data from NOMIS, we can use SmartGeocodeLookup:
las = ['Lewisham', 'Greenwich', 'Bromley', 'Southwark', 'Tower Hamlets']
gss = SmartGeocodeLookup(starting_column='OA21CD', ending_column='OA11CD', local_authorities=las)

geocodes = gss.get_filtered_geocodes()

# We can see that the the codes are actually in the same table.
print(geocodes)
#%% However, we need to get ward level information, so let's do
gss = SmartGeocodeLookup(starting_column='WD22CD', ending_column='WD11CD', local_authorities=las)

geocodes = gss.get_filtered_geocodes()

# Now, three tables have been joined together (left join). The first table was chosen based on the presence of  'WD22CD' and either 'LAD', 
# 'UTLA', or 'LTLA' columns. The following items in the list are then the table name and column by which the table was joined to the 
# previous table. SmartGeocodeLookup has chosen these automatically using a path finding algorithm. 

# Gotcha #1: when using Google Colab, using 'WD22CD' as the starting column in the above snippet for some reason results in the table 
# joining to fail. This is likely because of differences in how Linux and Windows behave. To get around this, I have made the starting 
# column 'LTLA22CD' in Google Colab which is present when printing the output. 
# On Windows, gss = SmartGeocodeLookup(starting_column='WD22CD', ending_column='WD11CD', local_authorities=las) should work just fine.


#%% Printing the geocodes, we can see that some columns have a lot of NaN values and that we didn't drop any columns when doing the joins.
print(geocodes) #  this new table happens to also contain the OA21CD and OA11CD columns, so we're going to stick with this lookup table

#%%  Let's use these geocodes to download only the appropriate rows from NOMIS:
    
# GOTCHA #2: The following will result in an error because the URL becomes too long, although it works fine on Google Colab
oa21cd = list(geocodes['OA21CD'].unique())
print(len(oa21cd))
health_2021_by_oa = conn.table_to_pandas(dataset='NM_2055_1', qualifiers={'geography': oa21cd}, value_or_percent='value') 


#%% Instead of downloading all at once we can break the download by local authority:

tables_to_join_2021 = []    

for la in las:
    la_subset1 = geocodes[geocodes['LTLA22NM']==la]
    la_subset2 = geocodes[geocodes['LAD22NM']==la]
    
    # GOTCHA #3: note that changing the column name here from 'LTLA22NM' to 'LAD22NM' reduces the output for some reason. 
    # The names should be exactly the same for London boroughs, but for some reason are not. Always check that the numbers match your expecetations.
    print('LTLA22NM and LAD22NM lengths are equal:', len(la_subset1)==len(la_subset2))
    print(len(list(la_subset1['OA21CD'].unique())), len(list(la_subset2['OA21CD'].unique())))
    
    oa21cd = list(la_subset1['OA21CD'].unique())          
    lapd = conn.table_to_pandas(dataset='NM_2055_1', qualifiers={'geography': oa21cd}, value_or_percent='value')
    tables_to_join_2021.append(lapd)

#%%
health_2021_by_oa = pd.concat(tables_to_join_2021)

#%% Let's do the same for 2011:

tables_to_join_2011 = []    

for la in las:
    la_subset = geocodes[geocodes['LTLA22NM']==la]  
    oa11cd = list(la_subset['OA11CD'].unique()) 
    
    print(oa11cd)  
    # GOTCHA #4: there may be NAN values mixed in and we need to remove those:
    oa11cd = [x for x in oa11cd if x == x]
    lapd = conn.table_to_pandas(dataset='NM_1546_1', qualifiers={'geography': oa11cd}, value_or_percent='value')
    tables_to_join_2011.append(lapd)

health_2011_by_oa = pd.concat(tables_to_join_2011)

print(len(health_2011_by_oa))  
#%% Q: why so many rows?  A: each level is given its own row:
print(health_2021_by_oa.head(10)) # C2021_HEALTH_6_NAME column has six levels for each Output Area
print(health_2011_by_oa.head(10)) # C_HEALTH_NAME column has six levels for each Output Area


#%% Now that we have Output Area level for both 2021 and 2011 censuses for our five local authorities, we can start massaging the data 
# into our desired format by pivoting them:
health_2021_pivot = health_2021_by_oa.pivot_table('OBS_VALUE', ['GEOGRAPHY'], 'C2021_HEALTH_6_NAME')
health_2011_pivot = health_2011_by_oa.pivot_table('OBS_VALUE', ['GEOGRAPHY'], 'C_HEALTH_NAME')

print(health_2021_pivot.head(10))
print(health_2011_pivot.head(10))
#%% To map ward level information, we'll first sum the appropriate rows in the pivot tables:

wards_2022 = list(geocodes['WD22NM'].unique())

oa_11_by_ward_22_dict = {'Ward': [], 'WD22CD':[], 'OA11CD': []}
oa_21_by_ward_22_dict = {'Ward': [], 'WD22CD':[],'OA21CD': []}
for ward in wards_2022:
    ward_subset = geocodes[geocodes['WD22NM'] == ward]
    ward_subset_2011 = ward_subset.dropna(subset=['OA11CD'])  # Again, need to drop NaN values
    ward_subset_2021 = ward_subset.dropna(subset=['OA21CD'])  # Again, need to drop NaN values
    ward_2022_by_oa11 = list(ward_subset_2011['OA11CD'].unique())
    ward_2022_by_oa21 = list(ward_subset_2021['OA21CD'].unique())
    print(len(ward_2022_by_oa11), len(ward_2022_by_oa21))  # There are different numbers of Output Areas in 2021 and 2011
    oa_11_by_ward_22_dict['Ward'].extend([ward for i in range(len(ward_2022_by_oa11))])
    oa_21_by_ward_22_dict['Ward'].extend([ward for i in range(len(ward_2022_by_oa21))])
    oa_11_by_ward_22_dict['WD22CD'].extend([list(ward_subset['WD22CD'].unique())[0] for i in range(len(ward_2022_by_oa11))])
    oa_21_by_ward_22_dict['WD22CD'].extend([list(ward_subset['WD22CD'].unique())[0] for i in range(len(ward_2022_by_oa21))])
    oa_11_by_ward_22_dict['OA11CD'].extend(ward_2022_by_oa11)
    oa_21_by_ward_22_dict['OA21CD'].extend(ward_2022_by_oa21)

oa_11_by_ward_22_df = pd.DataFrame(data=oa_11_by_ward_22_dict)
oa_21_by_ward_22_df = pd.DataFrame(data=oa_21_by_ward_22_dict)


health_2011_pivot_to_sum = health_2011_pivot.merge(right=oa_11_by_ward_22_df, how='left', right_on='OA11CD', left_on='GEOGRAPHY')
health_2011_summed = health_2011_pivot_to_sum.groupby("WD22CD").sum()

health_2021_pivot_to_sum = health_2021_pivot.merge(right=oa_21_by_ward_22_df, how='left', right_on='OA21CD', left_on='GEOGRAPHY')
health_2021_summed = health_2021_pivot_to_sum.groupby("WD22CD").sum()

print(health_2011_summed.head())
print(health_2021_summed.head())

#%% Get percentages

columns = list(health_2011_summed.columns)
for col in columns:
    true_values = [True for i in range(len(health_2011_summed[f"{col}"]))]
    percentages = (health_2011_summed[f"{col}"]/health_2011_summed['All categories: General health'])*100
    health_2011_summed[f'{col}_percent'] = health_2011_summed[f"{col}"].mask(true_values, percentages)


columns = list(health_2021_summed.columns)
for col in columns:
    true_values = [True for i in range(len(health_2021_summed[f"{col}"]))]
    percentages = (health_2021_summed[f"{col}"]/health_2021_summed['Total: All usual residents'])*100
    health_2021_summed[f'{col}_percent'] = health_2021_summed[f"{col}"].mask(true_values, percentages)

print(health_2011_summed.head())
print(health_2021_summed.head())

#%% To actually map these values, we'll have to import geopandas and import the ward boundaries, which we then restrict to our 2022 wards

import geopandas as gpd


#%%
all_bounds = gpd.read_file('./Wards_(December_2022)_Boundaries_GB_BFC.geojson')
#%%

wards_codes = list(geocodes['WD22CD'].unique())
ward_bounds = all_bounds[all_bounds['WD22CD'].isin(wards_codes)]
#ward_bounds['geometry'] = [reproject(x) for x in ward_bounds['geometry'].geometry]

#%%
ward_bound_by_2021_health = ward_bounds.merge(health_2021_summed, how='outer', left_on='WD22CD', right_on='WD22CD')
ward_bound_by_2021_health.plot('Very good health_percent', legend=True)

#%%
ward_bound_by_2011_health= ward_bounds.merge(health_2011_summed, how='outer', left_on='WD22CD', right_on='WD22CD')
ward_bound_by_2011_health.plot('Very good health_percent', legend=True)