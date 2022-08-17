from shapely.geometry import Polygon, MultiPolygon, box, MultiLineString, LinearRing
from shapely.ops import unary_union
import yaml
from pathlib import Path
import pandas as pd
import sys
import datetime as dt
import matplotlib.pyplot as plt
import geopandas as gpd
import mapclassify as mc
from matplotlib.dates import DateFormatter
from matplotlib.animation import FuncAnimation
from IPython import display as ipydisplay
# import base64
# import hashlib
# from typing import Callable
# from IPython.display import HTML, display, FileLink

######local imports
from Shapefile import subcountrymap
sys.path.append("..")
from PostGIS.GfasActivityReader import GfasActivityReader


class config_file():
    def __init__(self, 
                 DEFAULT_CONFIG_FILE: str = None
                ) -> None:
        
        if DEFAULT_CONFIG_FILE is not None:
            self.DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_FILE
        else:
            raise ValueError(""""The configuration file is not specified, it is not possible to run the wildfire emission explorer app.""")
        
        self.TOTAL_CONFIG = self.read_config()
    
    def read_config(self):    
        """Reads the config yaml file and transforms the indicated geometry in a shapely.geometry"""
        with open(self.DEFAULT_CONFIG_FILE) as src:
            dd = yaml.load(src, yaml.loader.FullLoader)
        if isinstance(dd['geometry'], list):
            if not isinstance(dd['geometry'][0], str):
                dd['geometry'] = self.recompose_polygon_from_coordinates(dd['geometry'], dd['polygon_type'])
            else:
                dd['geometry'] = self.recompose_polygon_from_countriesnames(dd['geometry'])
        else:
            dd['geometry'] = self.recompose_polygon_from_countriesnames(dd['geometry'])
        return dd
        
    def country_search(self, country_shapefile, name):
        """From a GeoPandas shapefile with names of continents/countries as index, find the corresponding geometry 
        of 'name' and only return it if a single one is found."""
        elements_found = country_shapefile[country_shapefile.index == name]
        if len(elements_found)==1:
            return elements_found.iloc[0].geometry
        else:
            raise ValueError(f"""The geometry name '{name}' contained in the config did not return a single result,
            N={len(elements_found)} matches were found. Please change this geometry name in the config and run again.""") 
    
    def multiple_country_search(self, country_shapefile, countrynames):
        all_geoms = []
        for cname in countrynames.split('+'):
            all_geoms.append(self.country_search(country_shapefile, cname))
        return unary_union(all_geoms)
            
    
    def recompose_polygon_from_countriesnames(self, countries_names):
        """From name(s) of a countries recompose a Polygon or Multipolygon.
        INPUTS:
         - countries_names: List or string with names of the countries in English.
        OUTPUTS:
         - geom: Polygon or Multipoligon geometry
         """      
        # GET SHAPEFILE
        url_to_download    = "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_map_units.zip"#"https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_50m_admin_0_countries.zip"
        file_path_location = '/home/esowc32/PROJECT/DATA/shapefiles/personalized_from_ne_110m_admin_0_map_units.geojson'
        sbcm = subcountrymap(file_path_location = file_path_location, url_to_download = url_to_download)
        countries  = sbcm.shapefile.copy()
        countries.index = countries.GEOUNIT
        all_shapes = pd.concat([countries, sbcm.continent_shapefile.copy()])[['geometry','continent']]
        all_shapes = all_shapes.groupby(all_shapes.index).last()
        if isinstance(countries_names, list):
            self.countryname = []
            all_geoms = []
            for name in countries_names:
                all_geoms.append(self.multiple_country_search(all_shapes, name))
            self.countryname = countries_names
            return all_geoms
        elif isinstance(countries_names,str):
            self.countryname = [countries_names]
            return [self.multiple_country_search(all_shapes, countries_names)]
    
    def recompose_polygon_from_coordinates(self, mpolxy, polygon_type):
        """From list of x,y coords (If MultiPolygon is a list of tuples, like:[(x,y),...]) 
        recompose a Polygon or Multipolygon.
        INPUTS:
         - polxy: List of x,y of the decomposed Polygon (or list of tuples for Multipolygon).
        OUTPUTS:
         - geom: Polygon or Multipoligon geometry
         """
        if (isinstance(mpolxy[0],tuple)) |(isinstance(mpolxy[0][0],list)):
            all_pol = []
            if polygon_type == 'multipolygon':
                for xx,yy in mpolxy:
                    all_pol.append([(xi,yi) for xi,yi in zip(xx,yy)])
                geom = MultiPolygon([Polygon(s) for s in all_pol])
            elif polygon_type == 'singlepolygon':
                exterior = LinearRing([(xi,yi) for xi,yi in zip(mpolxy[0][0],mpolxy[0][1])])
                interiors = []
                for xx,yy in mpolxy[1::]:
                    interiors.append(LinearRing([(xi,yi) for xi,yi in zip(xx,yy)]))
                geom = Polygon(exterior, interiors)
        else:
            geom = Polygon([(xi,yi) for xi,yi in zip(mpolxy[0],mpolxy[1])])
        return geom
    
    def decompose_polygon_for_config(self, geom):
        """Extracts coords of a Polygon or Multipolygon and returns a list of x,y coords 
        (If MultiPolygon is a list of tuples, like:[(x,y),...]).
        INPUTS:
         - geom: Polygon or Multipoligon geometry
        OUTPUTS:
         - polxy: List of x,y of the decomposed Polygon (or list of tuples for Multipolygon).
         """
        if isinstance(geom, str):
            return '',''
        lines = geom.boundary
        if isinstance(lines, MultiLineString):
            mpolxy = []
            for pol in lines.geoms:
                mpolxy.append([list(r) for r in pol.xy])
        else:
            mpolxy = [list(r) for r in lines.xy]
        if isinstance(geom, MultiPolygon):
            polygon_type = 'multipolygon'
        else:
            polygon_type = 'singlepolygon'

        return mpolxy, polygon_type

    
    
class query_data():
    def __init__(self, TOTAL_CONFIG: dict = None) -> None:
        self.table_database = {
                'Wildfire flux of Carbon Dioxide'           :('co2fire'  , 'gfas_co2fire_data',  'kg/day',),                   
                'Wildfire flux of Carbon Monoxide'          :('cofire'   , 'gfas_cofire_data',   'kg/day',),                                                        
                'Wildfire flux of Methane'                  :('ch4fire'  , 'gfas_ch4fire_data',  'kg/day',),                                               
                'Wildfire flux of Nitrogen Oxides NOx'      :('noxfire'  , 'gfas_noxfire_data',  'kg/day',),                              
                'Wildfire flux of Particulate Matter PM2.5' :('pm2p5fire', 'gfas_pm2p5fire_data','kg/day',),                                  
                'Wildfire flux of Total Particulate Matter' :('tpmfire'  , 'gfas_tpmfire_data',  'kg/day',),                      
                'Wildfire flux of Total Carbon in Aerosols' :('tcfire'   , 'gfas_tcfire_data',   'kg/day',),                               
                'Wildfire flux of Organic Carbon'           :('ocfire'   , 'gfas_ocfire_data',   'kg/day',),               
                'Wildfire flux of Black Carbon'             :('bcfire'   , 'gfas_bcfire_data',   'kg/day',),                              
                'Wildfire overall flux of burnt Carbon'     :('cfire'    , 'gfas_cfire_data',    'kg/day',),                                   
                'Wildfire radiative power'                  :('frpfire'  , 'gfas_frpfire_data',  'W',),                    
                'Wildfire Flux of Ammonia (NH3)'            :('nh3fire'  , 'gfas_nh3fire_data',  'kg/day',)
            }  
        
        if TOTAL_CONFIG is not None:
            self.TOTAL_CONFIG = TOTAL_CONFIG
            self.data = self.create_dataset_query()

    def adapt_resolution(self, data_or, resolution = None):
        """Function to resample the data at different resolutions ('daily' or 'monthly' for now)"""
        if resolution =='monthly':
            datanew = data_or.groupby([data_or.index.month,data_or.index.year]).mean()
            datanew.index = [pd.Timestamp(day = 1, month = f[0], year = f[1]) for f in datanew.index.values]
            datanew = datanew.sort_index()

        if resolution=='weekly':
            datanew = data_or.groupby(data_or.index.strftime('%Y-%U')).mean()
            datanew.index = [pd.to_datetime(f'{f[0:4]}-{(int(f[-2::]))*7+1}', format='%Y-%j') for f in datanew.index]
            datanew = datanew.sort_index()

        if resolution=='daily':
            datanew = data_or # they are already at a daily resolution
        return datanew

    def extract_data(self, adapt_resolution_option = True, 
                 start_date = None, 
                 end_date = None, 
                 function_to_aggregate = 'sum', 
                 keep_separate_dates = False,
                 reference_period = False):

        table_name = self.table_database[self.TOTAL_CONFIG['variable']][1]
        db = GfasActivityReader() #starts the connection with the database
        polygon = self.TOTAL_CONFIG['geometry']
        minx, miny,maxx, maxy = polygon.bounds
        start_date = dt.datetime.strptime(start_date,'%d-%m-%Y')
        end_date   = dt.datetime.strptime(end_date,'%d-%m-%Y')
        if start_date>end_date:
            raise ValueError(f'INVALID SPECIFIC PERIOD: start after end. Start={start_date:%d-%m-%Y}, End={end_date:%d-%m-%Y}')

        if '2D' in self.TOTAL_CONFIG['plot_type']: # index are now 'clust' 'x_y' info
            data_or, data = db.extract_data_polygon(table_name, start_date, end_date, polygon,
                                                    agg_operations = [function_to_aggregate],
                                                    resolution = 0.1, keep_separate_dates = keep_separate_dates)
            if data.empty:
                return data
            adapt_resolution_option = False
            start_date, end_date   = data_or.index[0], data_or.index[-1]
        else:
            data = db.extract_data2(start_date, end_date, polygon, table_name, agg_operation = function_to_aggregate)
            if data.empty:
                return data
            start_date, end_date   = data.index[0], data.index[-1]
            months_abbreviations = {'January':'Jan', 'February': 'Feb', 'March': 'Mar', 'April': 'Apr', 'May':   'May', 'June':  'Jun', 'July' : 'Jul', 'August':'Aug', 'September': 'Sept', 'October'  : 'Oct', 'November' : 'Nov', 'December' : 'Dec'}
            # AVERAGE SAME DAY OF DIFFERENT YEAR TOGETHER
            if not keep_separate_dates:
                data = data.groupby([f'{dd:02d}-{mm:02d}' for dd, mm in zip(data.index.day, data.index.month)]).mean()
                data.index = [pd.Timestamp(year = 2220, day = int(f[0:2]), month = int(f[3::])) for f in data.index]
                data.index = pd.DatetimeIndex(data.index)
        data.columns = [f"{start_date.day:02d}/{start_date.month:02d}/{start_date.year} - {end_date.day:02d}/{end_date.month:02d}/{end_date.year}" if (f!='geometry') else 'geometry' for f in data.columns]

        if adapt_resolution_option:
            return self.adapt_resolution(data.copy(), resolution = self.TOTAL_CONFIG['resolution'])
        else:
            return data.copy()
            
    def create_dataset_query(self):
        """Main functions that decides how to query the daat from the Database depending on the plot needed."""
        aggregating_operation = self.TOTAL_CONFIG['aggregating_operation']
        var = self.table_database[self.TOTAL_CONFIG['variable']][1] 

        if self.TOTAL_CONFIG['plot_type'] =='2D Animated Plot':
            data_to_plot = self.extract_data(start_date = self.TOTAL_CONFIG['specific_start_date'], 
                                        end_date = self.TOTAL_CONFIG['specific_end_date'], 
                                        function_to_aggregate = aggregating_operation,
                                        keep_separate_dates = True, 
                                        reference_period = False)
        else:
            data_to_plot = self.extract_data(start_date = self.TOTAL_CONFIG['specific_start_date'],
                                        end_date = self.TOTAL_CONFIG['specific_end_date'],
                                        function_to_aggregate = aggregating_operation)
            #ADD reference period
            if (self.TOTAL_CONFIG['reference_start_date']!='') & (self.TOTAL_CONFIG['reference_end_date']!='') & (self.TOTAL_CONFIG['plot_type'] !='2D Plot'):
                reference_data = self.extract_data(start_date = self.TOTAL_CONFIG['reference_start_date'],
                                              end_date = self.TOTAL_CONFIG['reference_end_date'],
                                              reference_period = True,
                                              function_to_aggregate = aggregating_operation
                                             )
                reference_data.rename(columns={c: f'REFERENCE: {c}' for c in reference_data.columns}, inplace=True)
                data_to_plot   = pd.merge( reference_data,data_to_plot, left_index=True, right_index=True)
            data_to_plot   = data_to_plot.sort_index()
        return data_to_plot
    
    
#             fig_sol, ax_sol = plot_config(data_to_plot, operation = aggregating_operation)
            
#             data_to_save   = data_to_plot.copy()
            
#             if self.TOTAL_CONFIG['plot_type'] !='2D Plot':
#                 data_to_save.index = [f"{dd.day:02d}-{dd.strftime('%b')}" for dd in data_to_save.index]

class plot_data():
    def __init__(self, 
             TOTAL_CONFIG: str = None,
             data_to_plot: pd.DataFrame = None,
             table_database: dict = None,
            ) -> None:    
        self.TOTAL_CONFIG   = TOTAL_CONFIG
        self.table_database = table_database
        self.data_to_plot   = data_to_plot
        
        self.fig_sol, self.ax_sol = plt.subplots(figsize = (8,5))
        self.fig_sol.tight_layout()
    
    def plot_lineplot(self, data, ax):
        """Creates a lineplot with quantiles (from 0 to 100 with different steps) for each day of the year."""
        ddoy = data.groupby(data.index.dayofyear)
        quantiles = [0, 0.1, 0.25, .5, .75, 0.9, 1]
        for p in quantiles:
            d = ddoy.quantile(p)
            d.rename(columns={c: f'p={p}%-{c}' for c in d.columns}, inplace=True)
            d.index = [pd.to_datetime(f'2000{f:03d}', format = '%Y%j') for f in d.index]
            if quantiles.index(p) == 0:
                ax = d.plot(ax=ax)
            else:
                d.plot(ax=ax)
        dfmt = DateFormatter("%d-%b") # proper formatting Year-month-day
        ax.xaxis.set_major_formatter(dfmt)
        return ax

    def plot_barplot(self, ax, title = None, resolution = None):
        """Creates the barplot using 'self.data_to_plot' in the specified axis 'ax'. 'resolution' is used to adapt the xaxis ticks."""
        if resolution is None:
            resolution = self.TOTAL_CONFIG['resolution']
        if title is None:
            title = f"{self.TOTAL_CONFIG['variable']}"

        self.data_to_plot.plot.bar(ax=ax, color = ['#A9A9A9','#B22222','y'])
        if resolution =='daily': # for daily data
            ax.set_xticklabels([f'{pd.Timestamp(f.get_text()).day:02d}-{pd.Timestamp(f.get_text()).month_name()}' for f in ax.get_xticklabels()])
            ax.locator_params(axis='x', nbins=12)
        else:
            ax.set_xticklabels([f'{pd.Timestamp(f.get_text()).month_name()}' for f in ax.get_xticklabels()])

        ax.set_title(title)    
        return ax

    def plot2dbackground(self, ax):
        """Function to create the background of the 2d plot, with boarders of the countries and the highlighted area of interest."""
        bb = self.TOTAL_CONFIG['geometry']
        elem = gpd.GeoDataFrame(geometry = [bb], crs = 'EPSG:4326')
        ax = elem.boundary.plot(ax=ax, zorder = 0, color = 'grey', alpha = 1, lw = 0.7)
        
        # GET SHAPEFILE
        url_to_download    = "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_map_units.zip"#"https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_50m_admin_0_countries.zip"
        file_path_location = '/home/esowc32/PROJECT/DATA/shapefiles/personalized_from_ne_110m_admin_0_map_units.geojson'
        sbcm = subcountrymap(file_path_location = file_path_location, url_to_download = url_to_download)
        countries  = sbcm.shapefile.copy()
        countries.index = countries.GEOUNIT
        all_shapes = pd.concat([countries, sbcm.continent_shapefile.copy()])[['geometry','continent']]
        all_shapes = all_shapes.groupby(all_shapes.index).last()
        
        ax = all_shapes.boundary.plot(ax=ax, color = 'grey', alpha =0.8, lw = 0.2)

        #extract limits
        ll = max(bb.bounds[2]-bb.bounds[0], bb.bounds[3]-bb.bounds[1])
        ## new squared geometry
        bbnew = box(bb.centroid.x-ll/2,bb.centroid.y-ll/2,bb.centroid.x+ll/2,bb.centroid.y+ll/2)
        xmin,ymin,xmax, ymax = bbnew.buffer(2).bounds
        ## set limits new
        ax.set_xlim(xmin,xmax)
        ax.set_ylim(ymin,ymax)
        return ax

    def plot_2dplot(self, data, ax, operation = 'sum', title = None, background = True, vmin=None, vmax=None, scheme='quantiles', classification_kwds=None):
        """Creates the 2D plot using the datas in 'self.data_to_plot' """

        table_name = self.table_database[self.TOTAL_CONFIG['variable']][1]
        unit_meas  = self.table_database[self.TOTAL_CONFIG['variable']][2]
        name_ext   = self.TOTAL_CONFIG['variable']

        column_name_to_plot = data.columns[0]#f"{table_name.replace('_data','')}_{operation}"
        st, en = data.columns[0].split(' - ')
        st = st.split('_')[-1]
        if title is None:
            title = f"{name_ext}\n '{operation}' from {st} to {en}"
        legend_name = f"{table_name} [{unit_meas.replace('/day','')}]"

        if background:
            ax = self.plot2dbackground(ax)

        data.plot(column_name_to_plot,
                     ax=ax, 
                     cmap='OrRd',#'RdYlBu_r', 
                     vmin = vmin, vmax = vmax,
                     legend=True, scheme=scheme,
                     k= 10,
                     classification_kwds=classification_kwds,
                     legend_kwds = dict(
                         loc='center left', 
                         bbox_to_anchor=(1, 0.5),
                         title = legend_name, fmt = '{:.1e}')
                      )
        ax.set_title(title)
        fig = ax.get_figure()
        fig.tight_layout()
        # correction: remove for first element of the legend which is always [-inf, 0]
        return ax

    def animate_plot_2dplot(self, all_days, ax_sol, operation = 'sum'):
        """Create an animation of the defined area"""
        
        scheme="User_Defined"
        val_min = all_days.iloc[:,0].min()
        val_max = all_days.iloc[:,0].max()
        classification_kwds=dict(bins=mc.Quantiles(all_days.iloc[:,0]).bins)

        indd = []
        for days in all_days.index.get_level_values(0).drop_duplicates():
            indd.append(days)
        pp = all_days.loc[[indd[0]],:]

        fig_sol = ax_sol.get_figure()
        fig_sol.tight_layout()

        self.plot_2dplot(pp, ax_sol, title = f"{self.TOTAL_CONFIG['variable']}\n{days.day:02d}-{days.month:02d}-{days.year}",
                    scheme=scheme, classification_kwds=classification_kwds,
                    )
        def animate(frame_num):
            #         text.value = f'2. Creating video {frame_num+1}/{len(indd)} completed'
            days = indd[frame_num]
            self.plot_2dplot(all_days.loc[days,:],
                        ax=ax_sol,
                        title = f"{self.TOTAL_CONFIG['variable']}\n{days.day:02d}-{days.month:02d}-{days.year}", 
                        background=False,scheme=scheme, classification_kwds=classification_kwds,
                       )
            return ax_sol
        plt.close()
        anim = FuncAnimation(fig_sol, animate, frames=len(indd), interval=250)
        video = anim.to_html5_video()
        html = ipydisplay.HTML(video)
        ipydisplay.display(html, clear= True )
        return anim

    def create_plot_type(self, countryname):
        config = self.TOTAL_CONFIG
        plot_type = config['plot_type']
        """Creates the plot"""
        if plot_type == 'Line Plot':
            self.ax_sol = self.plot_lineplot(self.data_to_plot, self.ax_sol)
            self.outfilename = f"LinePlot_{countryname}_from{config['specific_start_date']}to{config['specific_end_date']}.png"
        elif plot_type == 'Bar Plot':
            self.ax_sol = self.plot_barplot(self.ax_sol, resolution = self.TOTAL_CONFIG['resolution'])
            self.outfilename = f"BarPlot_{countryname}_from{config['specific_start_date']}to{config['specific_end_date']}.png"
        elif plot_type == '2D Plot':
            self.ax_sol = self.plot_2dplot(self.data_to_plot, self.ax_sol, operation = self.TOTAL_CONFIG['aggregating_operation'])
            self.outfilename = f"2DPlot_{countryname}_from{config['specific_start_date']}to{config['specific_end_date']}.png"
        elif plot_type == '2D Animated Plot':
            self.anim = self.animate_plot_2dplot(self.data_to_plot, self.ax_sol, operation = self.TOTAL_CONFIG['aggregating_operation'])
            self.outfilename = f"2DAnimatedPlot_{countryname}_from{config['specific_start_date']}to{config['specific_end_date']}.mp4"
            return self.anim, None
        else:
            raise ValueError(f"""The plot type in the configuration file is not any of ['Line Plot','Bar Plot','2D Plot','2D Animated Plot']""")
        return self.fig_sol, self.ax_sol
    
    def save_plot(self):
        plot_type = self.TOTAL_CONFIG['plot_type']
        outfilepath = Path(self.TOTAL_CONFIG['output_folder']) / self.outfilename
        if plot_type == '2D Animated Plot':
            self.anim.save(outfilepath)
        else:
            self.fig_sol.savefig(outfilepath, dpi = 300, facecolor = 'w')
    
if __name__ == '__main__':
    configfile = sys.argv[1]
    cf = config_file(configfile) #('/home/esowc32/PROJECT/DATA/test_config.yml')
    config = cf.TOTAL_CONFIG
    # CHECK OUTPUT FOLDER
    if not 'output_folder' in config.keys(): # if no path specified a new fodler is created in the current directory
        config['output_folder'] = Path.cwd() / f"outfolder_query_{dt.datetime.now().strftime(format='%d%m%YT%H%M%S')}"
    Path(config['output_folder']).mkdir(exist_ok= True, parents = True)

    for geom, cname in zip(config['geometry'], cf.countryname):
        print(cname)
        config2 = config.copy()
        config2.update({'geometry':geom})
        print('query')
        qd = query_data(config2)
        table_database = qd.table_database
        data = qd.data
        print('plot')
        plod = plot_data(config2, data, table_database)
        plod.create_plot_type(cname)
        plod.save_plot()
    
    