# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 12:30:54 2022

@author: ISipila
"""

from LBLDataAccess.access_nomis import DownloadFromNomis, NomisTable


#%%
gss = GeocodeLookup()

oa_2021_lewisham, table_name = gss.lad_bible(year='2021_to_2022', local_authority=['Lewisham', 'Waltham Forest'], geography='LAD')

print(oa_2021_lewisham)

#%%
new_connection = DownloadFromNomis()
new_connection.connect()


#%%
tables = new_connection.get_all_tables()
print(tables[0])


#%%
new_connection.print_table_info()
#%%
new_connection.detailed_info_for_table('NM_2097_1')

#%%
new_connection.short_description_for_table('NM_2097_1')
#%%
print(len(tables))
print(tables[0].detailed_description())
print(tables[0].get_table_cols())
print(tables[0].table_cols())
#%%
tables[0].table_shorthand()
#%%
for i in range(len(tables)):
    print(tables[i].id,':', tables[i].name['value'])

#%%

oas = list(set(list(oa_2021_lewisham['oa21cd'])))
print(len(oas))
#%%

"""
for oa in oas:
    new_connection.table_to_download(dataset='NM_2021_1', qualifiers=[('geography', [oa])], value_or_percent='value')
        
"""
#%%

df = new_connection.table_to_pandas(dataset='NM_2084_1', qualifiers={'geography': oas}, value_or_percent='value')


print(df)

#%%
import pandas as pd
pd.set_option('display.max_columns', None)
print(df.head(10))

#%%

df_subset = df[df['C2021_HIQUAL_8_CODE'].isin([f'_{num}' for num in range(7)])]

print(df_subset)

#%%
singular_cols = []
for col in list(df_subset.columns):
    num_unique = len(list(df_subset[col].unique()))
    if num_unique == 1:
        singular_cols.append(col)

df_dropped = df_subset.drop(singular_cols, axis=1)

print(df_dropped.head(10))

