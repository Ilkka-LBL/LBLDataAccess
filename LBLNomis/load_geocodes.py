# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 11:07:47 2022

@author: ISipila
"""
from pathlib import Path
import pandas as pd

class SelectGeocode:
    """
    Use this class to find the appropriate GSS codes for your local authority for use with ONS NOMIS API.

    Provide the name of the local authority or a known GSS code for the local authority.
    The get_wards method gives a list of GSS codes for wards. 
    Similarly, get_output_areas method gives a list of GSS codes for output areas.
    
    TODO:
        add more lookup tables
        Fix module structure so that no need to feed census_collection & follow the structure from 
        https://geoportal.statistics.gov.uk/search?collection=Dataset&sort=-created&tags=all(LUP_ADM)
        
    """
    
    def __init__(self, local_authority: str = 'Lewisham', census_collection: str = 'census_2021', gss_code: str = None, 
                 get_code_table: bool = False):
        """Initialize SelectGeocode."""        
        self.folder = Path(f'../lookups/{str(census_collection)}')  # path to lookup tables
        self.local_authority = local_authority.capitalize()
        self.gss_code = gss_code
        
        self.get_code_table = get_code_table
        
        self.df = None
        
        
    def get_wards(self, get_code_table: bool = False):
        """
        Get ward level GSS codes.
        
        You can also get all codes as a Pandas dataframe by setting get_code_table to True.
        """
        ward_csv = self.folder.joinpath('Ward_lookup.csv')            
        self.df = pd.read_csv(ward_csv)
       
        # if get_code_table is true, just return the Ward_lookup.csv as a Pandas dataframe.
        self._get_whole_table()
        
        local_authority_name_column = 'LAD21NM'
        local_authority_code_column = 'LAD21CD'
        
        output_columns = ['_WD21CD', 'WD21NM']
        
        subset = self._return_subset(local_authority_name_column, local_authority_code_column, output_columns)
        
        return subset
        
        
    def get_output_areas(self, level: str = 'all'):
        """
        Get output area level GSS codes.
        
        You can also get all codes as a Pandas dataframe by setting get_code_table to True.
        Similarly, you can choose the output area level by setting it as one of 'all' (for all levels), 'oa' (smallest Output Area), 
        'lsoa' (Lower layer Super Output Area), or 'msoa' (Middle layer Super Output Area).
        """
        output_area_csv = self.folder.joinpath('OA_lookup.csv')
        self.df = pd.read_csv(output_area_csv, encoding='latin-1', dtype='unicode')
        
        # if get_code_table is true, just return the OA_lookup.csv as a Pandas dataframe.
        self._get_whole_table()
        
        output_area_codes = {'all': ['oa21cd', 'lsoa21cd', 'msoa21cd'], 'oa': ['oa21cd'], 'lsoa': ['lsoa21cd'], 'msoa': ['msoa21cd']}
        output_columns = output_area_codes[level]
        
        local_authority_name_column = 'lad22nm'
        local_authority_code_column = 'lad22cd'
        
        subset = self._return_subset(local_authority_name_column, local_authority_code_column, output_columns)

        return subset
    
    def _get_whole_table(self):
        if self.get_code_table:
            return self.df
        else:
            pass
    
    def _return_subset(self, local_authority_name_column, local_authority_code_column, output_columns):
        if self.gss_code is None:
            subset = self.df[self.df[local_authority_name_column]==self.local_authority]
            
        else:
            subset = self.df[self.df[local_authority_code_column]==self.gss_code]
        subset = subset[output_columns]
        return subset
        
        
    def list_all_collections(self):
        """TODO: Clean the list of paths to show directory structure."""
        main_path = Path('../lookups')
        return list(main_path.iterdir())