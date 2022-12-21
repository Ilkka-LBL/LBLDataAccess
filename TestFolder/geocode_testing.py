# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 11:57:46 2022

@author: ISipila
"""

from LBLNomis.load_geocodes import SelectGeocode


new_geo = SelectGeocode(local_authority='Lewisham', census_collection='census_2021')

wards = new_geo.get_wards()
oas = new_geo.get_output_areas(level='oa')

print(oas)
print(wards)
print(new_geo.list_all_collections())