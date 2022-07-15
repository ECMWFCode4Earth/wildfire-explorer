# from typing import Iterator, List
from pathlib import Path
import requests
import io
import geopandas as gpd
import zipfile
import shutil

class subcountrymap():
    def __init__(self, 
                 file_path_location: str = None,
                 url_to_download: str = None,
                 driver: str ='ESRI Shapefile',
                 add_continent:bool = True) -> None:
        
        if file_path_location is None: #use current directory as location (it will be used tosave the shapefile)
            self.file_path_location = Path(f"./{url_to_download.split('/')[-1]}")
        else: #filepath used to read OR save the shapefile
            self.file_path_location = Path(file_path_location)
        self.driver = driver
        self.url = url_to_download 
        
        # create a self.shapefile with the data contained in 'file_path_location' or 'url_to_download'. 
        # saves final data into 'self.file_path_location'
        self.download_or_read(add_continent)
        
                
    def download_or_read(self, add_continent:bool = True):
        #read
        if not self.read_shapefile_from_local(): # if it is true then the shapefile is read
            #download
            if self.read_shapefile_from_url():
                print('download successful')
                if 'continent' not in self.shapefile.columns:
                    print('adding')
                    if 'CONTINENT' not in self.shapefile.columns:
                        if add_continent:
                            self.add_continent_to_shapefile()
                    else:
                        self.shapefile['continent'] = self.shapefile['CONTINENT'].copy()
                #save to local - zip file
                self.save_shapefile_to_local(driver = self.driver)
            else:
                print('DOWNLOAD FAILED! (check the url)')
                return
        else:
            if 'continent' not in self.shapefile.columns:
                if 'CONTINENT' not in self.shapefile.columns:
                    if add_continent:
                        self.add_continent_to_shapefile()
                else:
                    self.shapefile['continent'] = self.shapefile['CONTINENT'].copy()
                #save to local - zip file
                self.save_shapefile_to_local(driver = self.driver)
        # compute a continent shapefile - the shapefile has to have a colum == 'continent'
        if add_continent:
            self.dissolve_into_continents()
    
    def dissolve_into_continents(self):
        if 'continent' in self.shapefile.columns:
            self.continent_shapefile = self.shapefile.dissolve('continent').copy()
        else:
            print("No column called 'continent', not possible to aggegate the shapes into a continental map.")
        
    
    def read_shapefile_from_url(self):
        """
        Function to connect and read on the fly the zip files provided by 'https://www.naturalearthdata.com/downloads/'.
        The shapefile will be read into a GeoDataFrame.
        """
        if self.url is None:
            print("""In order to download you need to specify a correct filename of the shapefile,
                  go to https://www.naturalearthdata.com/downloads/
                  and copy the name of the zip file  you want to download! (and the url before the zipfile name)""")
            return False
        else: #in order to connect to the webpage the request header has to be added, otherwise you get HTTPError: 406 - Not Acceptable
            headers = requests.utils.default_headers()
            headers.update({
                    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
                })
            r = requests.get(self.url, headers=headers)
            if r.ok: #check if the connection can be established
                self.shapefile = gpd.read_file(io.BytesIO(r.content))
                return True
            else:
                print(f"""
                The connection was not stablish. HTTP Response: {r.status_code} - {r.reason}
                {self.url}
                """)
                return False
            
    def read_shapefile_from_local(self):
        """
        If a 'file_path_location' exists it reads the shapefile directly from there into a geopandas.GeoDataFrame.
        """
        
        if self.file_path_location.exists(): # check if there is actually a shapefile in the location
            self.shapefile = gpd.read_file(self.file_path_location)
            return True
        else:
            return False
        
    def save_shapefile_to_local(self,  driver: str ='ESRI Shapefile'):
        """If a 'file_path_location' is provided it saves the shapefile in there for future use (faster than donloading again).
        INPUTS:
            - filename: the name of the shapefile to save 
            - driver  : geopandas driver to use (e.g. 'GeoJSON' for geojson files)
        """
        
        if not self.file_path_location.exists(): # check if there is actually a shapefile in the location
            if self.file_path_location.suffix =='.zip':
                alt_path = Path(str(self.file_path_location).replace('.zip',''))
                self.shapefile.to_file(alt_path, driver = driver)
                with zipfile.ZipFile(self.file_path_location, 'w') as zipf:
                    for f in alt_path.glob("*"):
                        zipf.write(f, arcname=f.name)
                shutil.rmtree(alt_path)
            else:
                print('YEE')
                assert 'continent' in self.shapefile.columns
                self.shapefile.to_file(self.file_path_location, driver = driver)
                
        else:
            print(f'the file {self.file_path_location.name} already exists!')        
        
    def add_continent_to_shapefile(self):
        """When workng with 'ne_110m_admin_0_map_units.zip', since it has no continent value per country, it is added searching in the 
        default geopandas map (also taken from naturalEarth)"""
        
        countries  = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres')).sort_values('name')
        countries.index = countries.name
        continents_roughly = countries.dissolve('continent')
        
        def int_with_continents(point):
            sel = continents_roughly[continents_roughly.intersects(point)]
            if len(sel)==0:
        #         print(f'PROBLEM, NO CONTINENT! - {point}')
                return 'PROBLEM'
            if len(sel)>1:
                print('PROBLEM, MORE continents_roughly!')
            if len(sel)==1:
                return sel.index.values[0]

        self.shapefile['continent'] = self.shapefile.geometry.centroid.apply(int_with_continents)
        def find_continent_iso(el):
            if el is not None:
                sel = countries[countries.iso_a3==el]
                if len(sel)==0:
                    print(f'PROBLEM, NO CONTINENT! - {el}')
#                     sel
                if len(sel)>1:
                    print('PROBLEM, MORE continents_roughly!')
                if len(sel)==1:
                    return sel.continent.values[0]
        if 'SU_A3' in  self.shapefile.columns:
            self.shapefile.loc[self.shapefile.continent=='PROBLEM', 'continent'] = self.shapefile.loc[self.shapefile.continent=='PROBLEM', 'SU_A3'].apply(find_continent_iso)
        self.shapefile['continent'] = self.shapefile['continent'].values.astype(str)
        
        columns = ['NAME_EN','continent']+[f for f in self.shapefile.columns if ('continent' not in f)&('NAME_' not in f)&('FCLASS_' not in f)&('geometry' not in f)] + ['geometry']
        self.shapefile = self.shapefile[columns]