from requests import get as request_get
from dataclasses import dataclass
from typing import Any, Dict, List
import geopandas as gpd
import json
import re
from datetime import datetime
import pandas as pd 

@dataclass
class Service:
    name: str = None
    type: str = None
    url: str = None
    description: str = None
    layers: List[Dict[str, Any]] = None
    tables: List[Dict[str, Any]] = None
    output_formats: List[str] = None
    metadata: json = None
    fields: List[str] = None
    primary_key: str = None

    def featureservers(self) -> 'Service':
        if self.type == 'FeatureServer':
            return self

    def mapservers(self) -> 'Service':
        if self.type == 'MapServer':
            return self

    def wfsservers(self) -> 'Service':
        if self.type == 'WFSServer':
            return self

    def service_details(self) -> Any:
        service_url = f"{self.url}?&f=json"
        return request_get(service_url)
    
    def service_metadata(self) -> Any:
        service_url = f"{self.url}/0?f=json"
        return request_get(service_url)
        
    def service_attributes(self) -> None:
        service_info = self.service_details().json()
        self.description = service_info.get('description')
        self.layers = service_info.get('layers', [])
        self.tables = service_info.get('tables', [])
        self.output_formats = service_info.get('supportedQueryFormats', [])

        self.metadata = self.service_metadata().json()
        self.fields = self.metadata.get('fields', [])
        self.primary_key = self.metadata.get('uniqueIdField')
        lastedit = self.metadata.get('editingInfo', {})
        try:
            self.lasteditdate = lastedit['lastEditDate']  # in milliseconds - to get time, use datetime.fromtimestamp(int(og.feature_server.lasteditdate/1000)).strftime('%d-%m-%Y %H:%M:%S')
        except KeyError:
            self.lasteditdate = ''
        try:
            self.schemalasteditdate = lastedit['schemaLastEditDate']
        except KeyError:
            self.schemalasteditdate = ''        
        try:
            self.datalasteditdate = lastedit['dataLastEditDate']

        except KeyError:
            self.datalasteditdate = ''

    def lookup_format(self) -> Dict:
        self.service_attributes()
        try:
            row_data = {'name':[self.name], 'fields': [[field['name'] for field in self.fields]], 'url': [self.url], 'description': [self.description], 'primary_key': [self.primary_key['name']], 'lasteditdate': [datetime.fromtimestamp(int(self.lasteditdate/1000)).strftime('%d-%m-%Y %H:%M:%S')]}
        except TypeError:
            row_data = {'name':[self.name], 'fields': [[field['name'] for field in self.fields]], 'url': [self.url], 'description': [self.description], 'primary_key': [self.primary_key['name']], 'lasteditdate': ['']}
        return row_data

class BaseOpenGeography:

    def __init__(self) -> None:
        self.base_url = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services?f=json"
        self.output = request_get(self.base_url)
        self._validate_response()

        self.main_dict = self.output.json()
        self.services = self.main_dict.get('services', [])

        self._load_all_services()

        self.server_types = {'feature': 'FeatureServer', 'map': 'MapServer', 'wfs': 'WFSServer'}

    def _validate_response(self) -> None:
        assert self.output.status_code == 200, f"Request failed with status code: {self.output.status_code}"

    def _load_all_services(self) -> None:
        self.service_table = {}
        for service in self.services:
            service_obj = Service(service['name'], service['type'], service['url'])
            self.service_table[f"{service['name']}"] = service_obj

    def print_all_services(self) -> None:
        """
        Print name, type, and url of all services available through Open Geography Portal.
        """
        for service_name, service_obj in self.service_table.items():
            print(f"Service: {service_name}\nURL: {service_obj.url}\nServer type: {service_obj.type}\n")

    def print_services_by_server_type(self, server_type: str = 'feature') -> None:
        """
        Print services given a server type. The input to 'server_type' should be one of 'feature', 'map' or 'wfs'.
        Usually, it is enough to leave the server_type parameter unchanged, particularly as the MapServer and WFSServers
        are currently unsupported by this package.
        """

        if server_type == 'feature':
            for service in self.services:
                feature_server = self.service_table.get(f"{service['name']}").featureservers()
                if feature_server:
                    print('Service:', feature_server.name, '\nURL:', feature_server.url, '\nServer type:', feature_server.type, '\n')

        elif server_type == 'map':
            for service in self.services:
                map_server = self.service_table.get(f"{service['name']}").mapservers()
                if map_server:
                    print('Service:', map_server.name, '\nURL:', map_server.url, '\nServer type:', map_server.type, '\n')

        elif server_type == 'wfs':
            for service in self.services:
                wfs_server = self.service_table.get(f"{service['name']}").wfsservers()
                if wfs_server:
                    print('Service:', wfs_server.name, '\nURL:', wfs_server.url, '\nServer type:', wfs_server.type, '\n')

        else:
            print(f"{server_type} is not an identifiable server type. Try one of 'feature', 'map', or 'wfs'.")

    def make_lookup(self, service_type: str = 'feature', included_services: List[str] = []) -> pd.DataFrame:
        """
        Make a Pandas Dataframe of selected tables.
            - service_type (str): Select the type of server. Must be one of 'feature', 'map', 'wfs'. (default = 'feature').
            - included_services (List): An optional argument to select which services should be included in the set of tables to use for lookup. Each item of the list should be the name of the service excluding the type of server in brackets. E.g. ['Age_16_24_TTWA'].
        """
        
        assert service_type in ['feature', 'map', 'wfs'], "service_type not one of: 'feature', 'map', 'wfs'"

        if included_services:
            service_table_to_loop = {k: self.service_table.get(k, None) for k in included_services if k in self.service_table}

        else:
            service_table_to_loop = self.service_table

        lookup_table = []
        for service_name, service_obj in service_table_to_loop.items():
            if str(service_obj.type).lower() == self.server_types[service_type].lower():
                print(f"Adding service {service_name}")
                row_item = service_obj.lookup_format()
                lookup_table.append(row_item)

        print("Creating Pandas dataframe")
        lookup_dfs = [pd.DataFrame.from_dict(item) for item in lookup_table]
        
        if len(lookup_dfs) == 0:
            print("No valid data found. Exiting.")
            return
        else:
            lookup_df = pd.concat(lookup_dfs)
            return lookup_df

class FeatureServer(BaseOpenGeography):
    
    def select_service(self, service_name: str = None) -> None:
        """
        Select a service given its name.
        """
        try:
            self.service_name = service_name
            self.feature_server = self.service_table.get(self.service_name).featureservers()
            self.feature_server.service_attributes()

        except AttributeError as e:
            print(f"{e} - the selected table does not appear to have a feature server. Check table name exists in list of services or your spelling.")

    def service_details_json(self) -> Any:
        """
        Returns detailed information regarding the service as a json.
        """
        if hasattr(self, 'feature_server'):
            return self.feature_server.service_details().json()
        else:
            raise AttributeError("Choose service with select_service(service_name='') method first")

    def service_details_json(self) -> Any:
        """
        Returns the service metadata as a json.
        """
        if hasattr(self, 'feature_server'):
            return self.feature_server.service_metadata().json()
        else:
            raise AttributeError("Choose service with select_service(service_name='') method first")

    def service_attributes(self) -> None:
        """
        Prints key information about the service in an easily readable format.
        """
        if hasattr(self, 'feature_server'):
            print('Name:', self.feature_server.name)
            print('Description:', self.feature_server.description)
            print('Output formats:', self.feature_server.output_formats)
            print('Layers:', self.feature_server.layers)
            print('Tables:', self.feature_server.tables)
            print('Fields:', self.feature_server.fields)
            print('Primary key:', self.feature_server.primary_key)
        else:
            raise AttributeError("Choose service with select_service(service_name='') method first")


    def download(self, fileformat: str = 'geojson', sql_row_filter: str = '1=1', output_fields: str = '*', params: Dict = None, visit_all_links: bool = False, n_sample_rows: int = -1) -> List[Dict[str, Any]]:
        """
        Download data from Open Geography Portal.

        Parameters:
        - fileformat (str): The format in which to download the data (default: 'geojson').
        - sql_row_filter (str): SQL filter to apply to the rows (default: '1=1'). 
        - output_fields (str): Fields to include in the output (default: '*').
        - params (dict): If you want to manually override the search parameters. Only change if you cannot get the data otherwise. 
        - visit_all_links (bool): Some tables may have more than one link to visit. However, typically the first one is enough, so set this to True if you think you're missing data. Note that this method does not handle duplicate rows so you will have to deal with any duplication afterwards. 
        - n_sample_rows (int): This parameter helps with testing as it lets you quickly select the first n rows.

        Returns:
        - List[Dict[str, Any]]: List of dictionaries representing the downloaded data.
        """
        primary_key = self.feature_server.primary_key['name']

        assert isinstance(n_sample_rows, int), "n_sample_rows is not int"
        if n_sample_rows > 0 :
            sql_row_filter = f"{primary_key}<={n_sample_rows}"
        if not params or isinstance(params, dict):
            params = {
            'where': sql_row_filter,
            'objectIds': '',
            'time': '',
            'resultType': 'standard',
            'outFields': output_fields,
            'returnIdsOnly': False,
            'returnUniqueIdsOnly': False,
            'returnCountOnly': False,
            'returnDistinctValues': False,
            'cacheHint': False,
            'orderByFields': '',
            'groupByFieldsForStatistics': '',
            'outStatistics': '',
            'having': '',
            'resultOffset': '',
            'resultRecordCount': '',
            'sqlFormat': 'none',
            'f': fileformat
            }

        if hasattr(self, 'feature_server'):
            service_url = self.feature_server.url  # url for service
            
            # find all potential links for data:
            if self.feature_server.layers and self.feature_server.tables:
                links_to_visit = self.feature_server.layers
                links_to_visit.extend(self.feature_server.tables)
                fileformat = 'json'
            elif self.feature_server.tables:
                links_to_visit = self.feature_server.tables
                fileformat = 'json'
            elif self.feature_server.layers:
                links_to_visit = self.feature_server.layers

            link_url = f"{service_url}/{str(links_to_visit[0]['id'])}/query"  # visit first link
            print(f"Visiting link {link_url}")
            print(params['where'])
            response = request_get(link_url, params=params).json()  # get the first response
                       
            # use type checking to normalise the response
            if type(response) == dict:
                responses = json.dumps(response)
                responses = json.loads(responses)
            elif type(response) == str:
                responses = json.loads(response)
            
            count = self._record_count(link_url, sql_row_filter=params['where'])  # get the number of records to fetch given the parameters of the query
            counter = len(response['features'])  # number of initial features
            last_object = max([i["properties"][primary_key] for i in response["features"]])  # find ID of last item in query - will not work if primary key is not a simple counter, so may need to fix this. 
            print("Number of records:", count)
            print(count, last_object)

            pattern = r'>(\s*)(\d+)'
            while counter < int(count):
                # update the SQL where clause to reflect the number of objects already processed:
                if ">" in params['where']:
                    params['where'] = re.sub(pattern, '>' + str(last_object), params['where'], count=1)
                else:
                    params['where'] = f'{primary_key}>{last_object}'  
                additional_response = request_get(link_url, params=params).json()
                last_object = max([i["properties"][primary_key] for i in additional_response["features"]]) 
                responses['features'].extend(additional_response['features'])
                counter += len(additional_response['features'])
                print(counter, last_object)
                
            if len(links_to_visit) > 1 and visit_all_links:
                for link in links_to_visit[1:]:
                    print(f"Visiting link {link}")
                    link_url = f"{service_url}/{str(link['id'])}/query"
                    response = request_get(link_url, params=params).json()
                    count = self._record_count(link_url, sql_row_filter=params['where'])
                    counter = len(response['features'])
                    last_object = max([i["properties"][primary_key] for i in response["features"]])
                    print("Number of records:", count)
                    print(count, last_object)
                
                    while counter < int(count):
                        # update the SQL where clause to reflect the number of objects already processed:
                        if ">" in params['where']:
                            params['where'] = re.sub(pattern, '>' + str(last_object), params['where'], count=1)
                        else:
                            params['where'] = f'{primary_key}>{last_object}' 
                        additional_response = request_get(link_url, params=params).json()
                        last_object = max([i["properties"][primary_key] for i in additional_response["features"]])
                        responses['features'].extend(additional_response['features'])
                        counter += len(additional_response['features'])
                        print(counter, last_object)
            return responses
        else:
            raise AttributeError("Choose service with select_service(service_name='') method first")

    def _record_count(self, url: str, sql_row_filter: str = '1=1') -> int:
        params = {'returnCountOnly': True, 'where': sql_row_filter, 'f':'json'}
        return request_get(url, params=params).json()['count']

og = FeatureServer()