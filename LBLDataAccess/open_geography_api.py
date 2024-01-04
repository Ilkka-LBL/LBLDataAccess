from typing import Dict, List
from dataclasses import dataclass

class OpenGeography:
    def __init__(self, data_table: str = None, filter: Dict = {'1': '1'}, outfields: List = ['*']}) -> None:
                
        
        self.data_table = data_table
        if filter.keys[0] == '1':
            where_clause = '1%3D1'
        

        base_url = f"https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/{data_table}/FeatureServer/0/query?where={where_clause}&outFields={*}&f={geojson}&resultType=standard"
        #(BUA22NM%20IN%20('Lewisham'))
    
    def filter_clean(self):
        pass

    def outfield_clean(self):
        pass

    def filetype_clean(self):
        pass


    #https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/BUA_DEC_2022_EW_NC/FeatureServer/0/query?f=json&where=(BUA22NM%20IN%20('Lewisham'%2C%20'Southwark'%2C%20'Tower%20Hamlets'%2C%20'Greenwich'%2C%20'Bromley'%2C%20'Lambeth'))%20AND%20(BUA22CD%20IN%20('E63005035'))&outFields=*


if __name__ == '__main__':
    data_table = 'BUA_DEC_2022_EW_NC'