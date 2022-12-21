# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 12:30:54 2022

@author: ISipila
"""

#from LBLNomis.access_nomis import LBLToNomis
from LBLNomis.access_nomis import DownloadFromNomis

new_connection = DownloadFromNomis()
new_connection.connect()
tables = new_connection.get_all_tables()
print(len(tables))
print(tables[0].detailed_description())
print(tables[0].get_table_cols())

for i in range(len(tables)):
    print(tables[i].id,':', tables[i].name['value'])

oas = ['E00016136', 'E00016137', 'E00016138', 'E00016139']

for i in oas:
    new_connection.table_to_download('NM_2021_1', [('geography', i)])