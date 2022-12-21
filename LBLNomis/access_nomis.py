"""
Created on Wed Dec 14 10:50:56 2022.

@author: ISipila

Get a NOMIS api key by registering with NOMIS. 
Copy the api key (and nothing else) to a text file and name it 
NOMIS_KEY_API.txt. Place this text file in /api/ directory. Alternatively, 
provide the absolute path to the text file when creating a new LBLToNomis 
object.

There are two steps to downloading data from NOMIS. First, you need to 
understand 


"""

from pathlib import Path
import requests
from dataclasses import dataclass
from typing import List, Tuple
import shutil


class LBLToNomis:
    """Get NOMIS data using LBL proxies."""
    
    def __init__(self, api_key_location=None):
        """Initialize LBLToNomis."""
        # if api_key_location is not provided, see if NOMIS_KEY_API.txt exists
        if api_key_location is None:
            api_key_location = Path("../api/NOMIS_KEY_API.txt")
        
        assert api_key_location.exists(), "NOMIS_KEY_API.txt not found"
        
        # let's open the file and read the first line
        with api_key_location.open() as f:
            api_key = f.readline()
        
        self.uid = f"?uid={api_key}"  # this comes at the end of each call
        self.url = None  # initialize self.url
        
    def url_creator(self, 
                    dataset:str = None,
                    qualifiers: List[Tuple] = None, 
                    for_download: bool=False):
        """Create a URL string."""
        base_url = "http://www.nomisweb.co.uk/api/v01/dataset/"
        structure_URL = 'def.sdmx.json'
        
        if dataset is None:
            self.url = base_url+structure_URL+self.uid
            
        
        if for_download:
            table_url = base_url+dataset+'.data.csv?'
            for qualifier_tuple in qualifiers:
                # each qualifier tuple should consist of one understandable word
                # and one code. E.g. qualifier_tuple = ('geography', 1811939534) to get Lewisham for table NM_1_1
                table_url = f"{table_url}{qualifier_tuple[0]}={qualifier_tuple[1]}&"
            self.url = table_url+self.uid[1:]

            
    def connect(self, url:str = None):
        """Connect to NOMIS data to get the table structures."""
        # check if url has been provided, if not, create one.
        if url is None: 
            self.url_creator()
            
        # proxy address
        addrs = 'http://LBLSquidProxy.lblmain.lewisham.gov.uk:8080'
        self.proxies = {'http': addrs, 'https': addrs}
        
        # make the get call with proxies
        self.r = requests.get(self.url, proxies=self.proxies)
        
        
    def get_all_tables(self):
        """Get all available tables."""
        assert str(self.r) == "<Response [200]>"
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
    

class DownloadFromNomis(LBLToNomis):
    """Subclass for downloading data."""
    
    def __init__(self):
        """Initialize DownloadFromNomis."""
        super().__init__()
    
    def table_to_download(self,
                          dataset:str,
                          qualifiers: List[Tuple],
                          file_name: str = None,
                          save_location: str = '../nomis_download/',
                          value_or_percent: str = 'value'):
        """Download tables as csv files."""
        if value_or_percent == 'percent':
            qualifiers.append(('measures', 20301))
        else:
            qualifiers.append(('measures', 20100))

        self.url_creator(dataset, qualifiers, for_download=True)
        
        if file_name is None:
            file_name = f"{dataset}_with_{qualifiers[0][0]}_{qualifiers[0][1]}.csv"
        
        print(self.url, file_name)
        with requests.get(self.url, proxies=self.proxies, stream=True) as r:
            with open(file_name, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
            

    
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
        """Return a list of tuples where each tuple contains the column name and clean description."""
        columns = self.components['dimension']
        
        list_of_columns = [(col['codelist'], col['conceptref']) for col in columns]
        return list_of_columns
        
            
        