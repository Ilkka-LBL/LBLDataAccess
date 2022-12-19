# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 12:30:54 2022

@author: ISipila
"""

from LBLNomis.access_nomis import LBLToNomis

new_connection = LBLToNomis()
new_connection.connect()
tables = new_connection.get_available_tables()
print(len(tables))
print(tables[0].detailed_description())
print(tables[0])
print(tables[0].get_table_cols())