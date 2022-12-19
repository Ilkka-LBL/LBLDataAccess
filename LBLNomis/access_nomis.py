"""
Created on Wed Dec 14 10:50:56 2022.

@author: ISipila

Get a NOMIS api key by registering with NOMIS. Copy the api key (and nothing else) 
to a text file and name it NOMIS_KEY_API.txt. Place this text file in /api/ directory. 
Alternatively, provide the absolute path to the text file when creating a new LBLToNomis object.

"""

from pathlib import Path
import os
import requests
import pandas as pd
from dataclasses import dataclass


class LBLToNomis:
    """Get NOMIS data using LBL proxies."""
    
    def __init__(self, api_key_location=None):
        self.proxies = {'http': 'http://LBLSquidProxy.lblmain.lewisham.gov.uk:8080',
                   'https': 'http://LBLSquidProxy.lblmain.lewisham.gov.uk:8080'}
        if api_key_location is None:
            api_key_location = Path("../api/NOMIS_KEY_API.txt")
        
        with api_key_location.open() as f:
            api_key = f.readline()
        self.table_structure_URL=f'http://www.nomisweb.co.uk/api/v01/dataset/def.sdmx.json?uid={api_key}'
        
        
    def connect(self):
        """Connect to NOMIS data to get the table structures."""
        self.r = requests.get(self.table_structure_URL, proxies=self.proxies)
        
        
    def get_available_tables(self):
        """Get all available tables."""
        main_dict = self.r.json()
        get_annotations = main_dict['structure']['keyfamilies']['keyfamily']
        all_tables = []
        for data in get_annotations:
            keys = data.keys()
            if 'description' in list(keys):
                all_tables.append(NomisTable(data['agencyid'], 
                                             data['annotations'],
                                             data['id'],
                                             data['components'],
                                             data['description'],
                                             data['name'],
                                             data['uri'],
                                             data['version']))
            else:
                all_tables.append(NomisTable(data['agencyid'], 
                                             data['annotations'],
                                             data['id'],
                                             data['components'],
                                             data['name'],
                                             data['uri'],
                                             data['version']))
        return all_tables 
    
@dataclass
class NomisTable:
    """Dataclass that helps with structuring the output from NOMIS."""
    
    agencyid: str
    annotations: str
    id: str 
    components: str 
    name: str
    uri: str
    version: str
    description: str = None
    
    def detailed_description(self):
        """Get a detailed and cleaned overview of what the table is for."""
        print(f"\nTable id: {self.id}\n")
        
        print(f"Table description: {self.name['value']}\n")
        for table_annotation in self.clean_annotations():
            print(table_annotation)
        print("\n")
        for column_codes in self.table_cols():
            print(column_codes)
    
    def clean_annotations(self):
        """Simply cleaning the annotations for more readable presentation."""
        annotation_list = self.annotations['annotation']
        cleaned_annotations = list()
        for item in annotation_list:
            text_per_line = f"{item['annotationtitle']}: {item['annotationtext']}"
            cleaned_annotations.append(text_per_line)
        return cleaned_annotations
    
    def table_cols(self):
        """Simply cleaning the column information for a given table."""
        columns = self.components['dimension']
        col_descriptions_and_codes = list()
        for col in columns:
            text_per_line = f"Column: {col['conceptref']}, column code: {col['codelist']}"
            col_descriptions_and_codes.append(text_per_line)
        return col_descriptions_and_codes
    
    def get_table_cols(self):
        """Returns a list of tuples where each tuple contains the column name and clean description"""
        columns = self.components['dimension']
        
        list_of_columns = [(col['codelist'], col['conceptref']) for col in columns]
        return list_of_columns
        
        