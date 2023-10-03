"""
Created on Wed Dec 14 10:50:56 2022.

@author: ISipila

Get a NOMIS api key by registering with NOMIS. When initialising the DownloadFromNomis class, provide the api key as a parameter to the 
api_key argument. If you need proxies to access the data, provide the information as a dictionary to proxies. There is also a convenience 
argument to memorize these settings for later. For example:
    
    api_key = '02bdlfsjkd3idk32j3jeaasd2'                                # this is an example of random string from NOMIS website
    proxies = {'http': your_proxy_address, 'https': your_proxy_address}  # proxy dictionary must follow this pattern. If you only have http
                                                                         # proxy, copy it to the https without changing it

    connect_to_nomis = DownloadFromNomis(api_key=api_key, proxies=proxies, memorize=True)
    connect_to_nomis.connect()


"""

from pathlib import Path
from requests import get as requestget
from dataclasses import dataclass
from typing import List, Dict, Any
from shutil import copyfileobj
import pandas as pd
from pkg_resources import resource_stream
import json
from sys import exit

class LBLToNomis:
    """ Get NOMIS data.
        api_key: Nomis API key
        proxies: http and https proxy addresses as a dictionary object {'http': http_addr, 'https': https_addr} - this is optional
        memorize: set to True if you want to save API key and proxies in a plain text file.
    """
    
    def __init__(self, api_key: str = None, proxies: Dict = None, memorize: bool = False):
        """Initialize LBLToNomis."""
        # if api_key is not provided, see if config file exists. If it doesn't, and memorize is set to true, create a config file.
        
        try:
            self.config = json.load(resource_stream('LBLDataAccess', 'config/config.json'))
            self.api_key = self.config['nomis_api_key'].strip()
            assert self.api_key, "NOMIS api key not found in config/config.json - try setting it with the api_key argument and set memorize = True to store the key for later."
        except FileNotFoundError:
            if memorize:
                self._write_config_file(api_key=api_key, proxies=proxies)
                self.config = json.load(resource_stream('LBLDataAccess', 'config/config.json'))
                self.api_key = self.config['nomis_api_key'].strip()
            else:
                assert api_key, "NOMIS api key not set - try setting it with the api_key argument. You can also set memorize = True to store the key for later."
                self.api_key = str(api_key).strip()
                self.config = {'nomis_api_key': self.api_key, 'proxies': proxies}
                
        self.uid = f"?uid={self.api_key}"  # this comes at the end of each call
        
        self.base_url = "http://www.nomisweb.co.uk/api/v01/dataset/"
        self.url = None  # initialize self.url
        
    
    def reset_config(self):
        """Delete the configuration file and related information."""
        parent_path = Path(__file__).resolve().parent
        config_file_path = parent_path.joinpath('config/config.json')
        config_file_path.unlink()
        del self.api_key
        del self.proxies
    
    def update_config(self, api_key: str = None, proxies: Dict = None):
        """Update configuration file using the given api key and/or proxies."""
        if api_key:
            self.api_key = api_key
        new_proxies = {}
        for protocol, address in proxies.items():
            if address:
                new_proxies[protocol] = address
        self.proxies=new_proxies
        self._write_config_file(api_key=self.api_key, proxies=self.proxies)
        
    def _write_config_file(self, api_key: str = None, proxies: Dict = None):
        """Write configuration file given api key and/or proxies."""
        parent_path = Path(__file__).resolve().parent
        config_file_path = parent_path.joinpath('config/config.json')
        
        if config_file_path.is_file():
            with open(config_file_path) as json_data:
                config_file = json.load(json_data)
            json_data.close()
            
        else:
            config_file = {}
            if not parent_path.joinpath('config').is_dir():
                parent_path.joinpath('config').mkdir()
            config_file_path.touch()
        
        if api_key:
            config_file['nomis_api_key'] = str(api_key).strip()
        else:
            print('No API key provided nor was one found in the config file. Please provide an API key string.')
            exit()
        if proxies:
            proxy_formatting = "\nproxies = {'https': 'your_https_proxy', 'http': 'your_http_proxy'}"
            assert isinstance(proxies, dict), f"Proxies need to be given as a dictionary: {proxy_formatting}"

            try:
                http_proxy = proxies['http']
                https_proxy = proxies['https']
                config_file['proxies'] = {'http': http_proxy, 'https': https_proxy}

            except KeyError:
                print(f"Wrong format of proxy dictionary. The correct format is: {proxy_formatting}")

        with open(config_file_path, 'w') as f:                
            json.dump(config_file, f, sort_keys=True, indent=4, ensure_ascii=False)
        
    def bulk_download(self, dataset: str = None):
        """Create a URL string for bulk download."""
        table_url = self.base_url+dataset+'.bulk.csv?'
        self.url = table_url+self.uid[1:]
        self.url = self.url.strip()

    
    def url_creator(self, 
                    dataset: str = None,
                    qualifiers: Dict[str, List[str]] = None, 
                    select_columns: List[str] = None,
                    for_download: bool = False,
                    get_bulk: bool = False):
        """Create a URL string."""
        structure_URL = 'def.sdmx.json'
        
        if dataset is None:
            self.url = self.base_url+structure_URL+self.uid
        
        if for_download:
            table_url = self.base_url+dataset+'.data.csv?'
            if qualifiers:
                for keyword, qualifier_codes in qualifiers.items():
                    #print(keyword, qualifier_codes)
                    # each qualifier should consist of one understandable word and a list of codes. 
                    # E.g. keyword = 'geography', qualifier_codes = ['E09000023'] to get data for Lewisham.
                    # if the second part of the qualifier tuple is a list, however, we can make a custom call:
                    assert isinstance(qualifier_codes, list), print('Ensure qualifiers take the form Dict[str: List[str]]')
                    if len(qualifier_codes) == 1:
                        search_string = f"{qualifier_codes[0]}"
                    elif keyword == 'geography':
                        search_string = self._unpack_geography_list(qualifier_codes)
                    
                    else:
                        search_string = ''
                        
                        for qualifier_code in qualifier_codes:
                            search_string += f"{qualifier_code},"
                        search_string = search_string[:-1]
                        
                    table_url = f"{table_url}{keyword}={search_string}&"
                    
            if select_columns:
                selection = 'select='
                for col in select_columns:
                    selection += f'{col},'
                table_url = table_url+selection+'&'
            self.url = table_url+self.uid[1:]
            self.url = self.url.strip()
            
            
    def connect(self, url: str = None):
        """Connect to NOMIS data to get the table structures."""
        # check if url has been provided, if not, create one.
        if url is None: 
            self.url_creator()
            
        # if proxies haven't been manually set, but there is a config file, try finding proxies in the config file. If not there, try 
        # connecting to NOMIS without the proxies. If this fails, prompt the user to add proxies.

        try:
            if self.config['proxies']:
                self.proxies = self.config['proxies']
                # make the get call with proxies
                self.r = requestget(self.url, proxies=self.proxies)
            else:
                print(f"Proxies not set, attempting to connect without proxies")
                # make the get call with proxies
                self.r = requestget(self.url)
        except KeyError as e:
            print(f"{e} - proxies not set, attempting to connect without proxies")
            # make the get call with proxies
            self.r = requestget(self.url)
        
        if str(self.r) == '<Response [200]>':
            print("Connection okay")
        else:
            print('Could not connect to NOMIS. Have you set your proxies?')
        
    def get_all_tables(self) -> List[Any]:
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
    
    
    def print_table_info(self):
        """Print information for all tables."""
        tables = self.get_all_tables()
        for table in tables:
            table.table_shorthand()

    def detailed_info_for_table(self, table_name):
        """Print information for a chosen table."""
        table = self._find_exact_table(table_name)
        table.detailed_description()
        
    def _find_exact_table(self, table_name):
        """Loop through all tables and return the matching table name."""
        tables = self.get_all_tables()
        for table in tables:
            if table.id == table_name:
                return table
            
    def _geography_edges(self, nums) -> List[Any]:
        """Find edges in a list of integers."""
        nums = sorted(set(nums))
        gaps = [[s, e] for s, e in zip(nums, nums[1:]) if s+1 < e]
        edges = iter(nums[:1] + sum(gaps, []) + nums[-1:])
        return list(zip(edges, edges))

    def _create_geography_e_code(self, val) -> str:
        """Create a nine character GSS code (e.g. Exxxxxxxx)."""
        present_len = len(str(val))
        present_num_diff = 8-present_len
        zeroes = '0'*present_num_diff 
        present_code = f"E{zeroes}{val}"
        return present_code
    
    def _unpack_geography_list(self, geographies: List[str]) -> str:
        """Unpack a list of GSS codes, find the edges and format for URL."""
        sorted_geo = sorted(geographies)
        edited_geo = [int(i[1:]) for i in sorted_geo] 
        edges_list = self._geography_edges(edited_geo)
        list_to_concat = []
        for edge in edges_list:
            if edge[1] == edge[0]:
                present_code = self._create_geography_e_code(edge[0])
                list_to_concat.append(present_code)
                
            elif edge[1] - edge[0] == 1:
                first_present = self._create_geography_e_code(edge[0])
                second_present = self._create_geography_e_code(edge[1])
                list_to_concat.append(first_present)
                list_to_concat.append(second_present)
            else:
                first_present = self._create_geography_e_code(edge[0])
                second_present = self._create_geography_e_code(edge[1])
                long_code = f'{first_present}...{second_present}'
                list_to_concat.append(long_code)

        geography_str = ','.join(list_to_concat)
        return geography_str
    
    
class DownloadFromNomis(LBLToNomis):
    """Subclass for downloading data."""
    
    def __init__(self, *args, **kwargs):
        """Initialize DownloadFromNomis."""
        super().__init__(*args, **kwargs)
    
    def table_to_csv(self,
                          dataset: str = None,
                          qualifiers: Dict[str, List] = {'geography': None},
                          file_name: str = None,
                          table_columns: List[str] = None,
                          save_location: str = '../nomis_download/',
                          value_or_percent: str = None):
        """
        Download tables as csv files.
        
        Provide a dataset string (e.g. NM_2021_1), qualifier dictionary (e.g. {'geography':, [E00016136], 'age': [0, 2, 3]}), optional file 
        name, table columns if you know you want to limit the selection, a location to save the csv file (default is ../nomis_download/) and 
        whether you want the data as raw values or as percentages. You can leave value_or_percent empty to get both values and percentages.
        
        You can get the list of appropriate geography codes using SmartGeocodeLookup class from LBLNomis.load_geocodes script. While the 
        geography codes in Nomis do use ONS internal numbers, it's easier to select the right regions using GSS codes.
        
        Likewise, you can select a dataset using the get_all_tables() method, printing the resulting list, and choosing the table that is 
        the most appropriate for your task.
        """
        if value_or_percent == 'percent':
            qualifiers['measures'] = [20301]
            
        elif value_or_percent == 'value':
            qualifiers['measures'] = [20100]
        
        self.url_creator(dataset, qualifiers, table_columns, for_download=True)  
        
        if file_name is None:
            file_name = f"{dataset}_query.csv"
        
        if Path(save_location).exists() is False:
            Path(save_location).mkdir(parents=True, exist_ok=True)
            
        file_name = Path(save_location).joinpath(file_name)
        try:
            with requestget(self.url, proxies=self.proxies, stream=True) as r:
                with open(file_name, 'wb') as f:
                    copyfileobj(r.raw, f)
        except AttributeError:
            with requestget(self.url, stream=True) as r:
                with open(file_name, 'wb') as f:
                    copyfileobj(r.raw, f)

    
    def get_bulk(self, dataset: str = None, data_format: str = 'pandas', save_location: str = '../nomis_download/'):
        """Download bulk data as csv or as Pandas dataframe."""
        self.bulk_download(dataset)
        if data_format == 'csv' or data_format=='download':
            file_name = f"{dataset}_bulk.csv"
            
            if Path(save_location).exists() is False:
                Path(save_location).mkdir(parents=True, exist_ok=True)
                
            file_name = Path(save_location).joinpath(file_name)
            try:
                with requestget(self.url, proxies=self.proxies, stream=True) as r:
                    with open(file_name, 'wb') as f:
                        copyfileobj(r.raw, f)
            except AttributeError:
                with requestget(self.url, stream=True) as r:
                    with open(file_name, 'wb') as f:
                        copyfileobj(r.raw, f)
                
        elif data_format == 'pandas' or data_format == 'df':
            try:
                with requestget(self.url, proxies=self.proxies, stream=True) as r:
                    raw_text = pd.read_csv(r.raw)
                return raw_text
            except AttributeError:
                with requestget(self.url, stream=True) as r:
                    raw_text = pd.read_csv(r.raw)
                return raw_text

            
    def table_to_pandas(self,
                          dataset: str = None,
                          qualifiers: Dict[str, List] = {'geography': None},
                          file_name: str = None,
                          table_columns: List[str] = None,
                          value_or_percent: str = None):
        """
        Download tables to pandas.
        
        Provide a dataset string (e.g. NM_2021_1), qualifier dictionary (e.g. {'geography':, [E00016136], 'age': [0, 2, 3]}), optional file 
        name, table columns if you know you want to limit the selection, a location to save the csv file (default is ../nomis_download/) and 
        whether you want the data as raw values or as percentages. You can leave value_or_percent empty to get both values and percentages.
        
        You can get the list of appropriate geography codes using SmartGeocodeLookup class from LBLNomis.load_geocodes script. While the 
        geography codes in Nomis do use ONS internal numbers, it's easier to select the right regions using GSS codes.
        
        Likewise, you can select a dataset using the get_all_tables() method, printing the resulting list, and choosing the table that is 
        the most appropriate for your task.
        """
        if value_or_percent == 'percent':
            qualifiers['measures'] = [20301]
            
        elif value_or_percent == 'value':
            qualifiers['measures'] = [20100]
        self.url_creator(dataset, qualifiers, table_columns, for_download=True)
        try:
            with requestget(self.url, proxies=self.proxies, stream=True) as r:
                raw_text = pd.read_csv(r.raw)
            return raw_text
        except AttributeError:
            with requestget(self.url, stream=True) as r:
                raw_text = pd.read_csv(r.raw)
            return raw_text

    
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
    
    def clean_annotations(self) -> List[str]:
        """Clean the annotations for more readable presentation."""
        annotation_list = self.annotations['annotation']
        cleaned_annotations = list()
        for item in annotation_list:
            text_per_line = f"{item['annotationtitle']}: {item['annotationtext']}"
            cleaned_annotations.append(text_per_line)
        return cleaned_annotations
    
    def table_cols(self) -> List[str]:
        """Clean the column information for a given table."""
        columns = self.components['dimension']
        col_descriptions_and_codes = list()
        for col in columns:
            text_per_line = f"Column: {col['conceptref']}, column code: {col['codelist']}"
            col_descriptions_and_codes.append(text_per_line)
        return col_descriptions_and_codes
    
    def get_table_cols(self) -> List[str]:
        """Return a list of tuples where each tuple contains the column name and clean description."""
        columns = self.components['dimension']
        
        list_of_columns = [(col['codelist'], col['conceptref']) for col in columns]
        return list_of_columns
        
    def table_shorthand(self):
        """Return table id and simple description."""
        print(self.id,':', self.name['value'])
        
    
def _test_nomis():
    new_connection = DownloadFromNomis()
    new_connection.connect()
    
    if str(new_connection.r) == '<Response [200]>':
        print("Connection okay")
        
if __name__ == '__main__':
    _test_nomis()