from datetime import datetime
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import matplotlib.pyplot as plt
import psycopg2
from shapely import wkt
# ST_MakePolygon(ST_GeomFromText('LINESTRING(-88.4646835327148 40.2789344787598 231.220825195312, -88.4761428833008 40.2101783752441 223.626693725586,-88.4646835327148 40.2159080505371 235.470901489258,-88.4646835327148 40.2789344787598 231.220825195312,-88.4646835327148 40.2789344787598 231.220825195312)')), 4326)


class GfasActivityReader(object):

    conn = None
    cur = None

    def __init__(self):
        
        try:
            self.conn = psycopg2.connect("dbname='wfdb' user='wfuser' host='localhost'")
        except:
            print("I am unable to connect to the database")
            
        if self.conn is None:
            raise ConnectionError("It was not possible to connect to the PostGIS database, please contact the administration to review permissions.")
            
        self.cur = self.conn.cursor()
    
    def aggregate_by_cluster(self, data=None, res = 0.1, functions = None, columns_to_group = None):
        """Transform a GeoDataFrame of points geometry into square of resolution of 'res' degrees". All points contained in the grid
        of 'res' degrees are aggregated together"""   
        
        def get_boxes_from_index(poi, buf = res):
            xx,yy = [float(f) for f in poi.split('_')]
            return box(xx, yy, xx+buf, yy+buf)
        
        factor= 1/res
        data['clust'] = [f'{xx}_{yy}' for xx,yy in zip((np.floor(data.geometry.x*factor))/factor,
                                                       (np.floor(data.geometry.y*factor))/factor)]
        if 'clust' not in columns_to_group:
            columns_to_group.append('clust')
        data_aggr = data.groupby(columns_to_group).agg(functions)

        # just to check if the index is a multiindex
        if isinstance(data_aggr.index.values[0],tuple):
            level = len(data_aggr.index.values[0])-1
        else:
            level = 0
        # add geometry column
        geom = pd.Series(data_aggr.index.get_level_values(level),
                                      index=data_aggr.index).apply(get_boxes_from_index)
        data_aggr = gpd.GeoDataFrame(data_aggr, geometry = geom, crs = 'EPSG:4326')

        #rename columns (transform multicolumns in columns)
        new_cols = ['_'.join(tt) for tt in data_aggr.columns]
        new_cols = [f[:-1] if f[-1]=='_' else f for f in new_cols]
        data_aggr.columns = new_cols
        
        #'geom' column needs to be dropped
        cols_to_drop = [col for col in data_aggr.columns if ('geom' in col) & (col!='geometry')]
        data_aggr.drop(columns = cols_to_drop, inplace = True)
        
        return data_aggr

    def query(self, query, params):

#         self.cur.execute(query, params)
        df = pd.read_sql_query(query, self.conn,
                            params = params)
        df = df.set_index(['datetime'])
        return df

    def extract_data(self, start_date, end_date, nlat, slat, wlon, elon, table_name):

        query = f"""SELECT datetime, sum(value) FROM {table_name}
                WHERE datetime >= %(start_date)s AND datetime <= %(end_date)s AND
                geom && ST_MakeEnvelope(%(wlon)s, %(slat)s, %(elon)s, %(nlat)s, 4326)
                GROUP BY datetime 
                ORDER BY datetime;"""
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'nlat': nlat,
            'slat': slat,
            'wlon': wlon,
            'elon': elon
        }
        data = self.query(query, params)
        return data
    
    def extract_data2(self, start_date, end_date, polygon, table_name, agg_operation = None):
        """Extract aggregation operator (like 'sum' or 'mean') of all values for every single day for the region selected,
        return one value per day"""
        sql_conversion = {'mean':'AVG','median':'median','std':'stddev','min':'MIN','max':'MAX','sum':'SUM'}
        
        if agg_operation is None:
            agg_operation = 'SUM'
        else:
            agg_operation = sql_conversion[agg_operation]

        query = f"""SELECT datetime, {agg_operation}(value) FROM {table_name}
                WHERE datetime >= %(start_date)s AND datetime <= %(end_date)s AND
                ST_Contains(ST_GeomFromText('{polygon.wkt}', 4326), geom)
                GROUP BY datetime 
                ORDER BY datetime;"""
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        data = self.query(query, params)
#         print(query)
#         print(data.sum().iloc[0])
        return data
    
    def extract_data_polygon(self, table_name, start_date, end_date, polygon, agg_operations = None, resolution = 0.1, keep_separate_dates = True, aggregate = True):
        if agg_operations is None:
            agg_operations = ['sum'] #['sum','mean','std','max','min','count']
        if isinstance(agg_operations, str):
            agg_operations = [agg_operations]
        var_name = table_name.replace('_data','')
        
        query_pandas = f"""SELECT datetime, ST_AsText(geom) AS geom, value as {var_name} FROM {table_name}
                WHERE datetime >= %(start_date)s AND datetime <= %(end_date)s AND
                ST_Contains(ST_GeomFromText('{polygon.wkt}', 4326), geom)
                ORDER BY datetime;"""
        params = {
            'start_date': start_date,
            'end_date': end_date,
        }
        data = self.query(query_pandas, params)
        
        data['geom'] = data.geom.apply(wkt.loads)
        data = gpd.GeoDataFrame(data, geometry = data['geom'])
        if data.empty:
            return data, data
        # AGGREGATE BY CLUSTER
        if keep_separate_dates:
            cols_to_group = ['datetime','clust']
        else:
            cols_to_group = ['clust']
            
        if aggregate:
            data_aggregated = self.aggregate_by_cluster(data = data, res = resolution, 
                                                        functions = agg_operations, #['sum','mean','std','max','min','count'],
                                                        columns_to_group = cols_to_group)
        else:
            data_aggregated = None
            
        return data, data_aggregated


    def __del__(self):
        self.cur.close()
        self.conn.close()


def main():

    db = GfasActivityReader()

    (nlat, slat, wlon, elon) = (0, -8, 108, 120)
    start_date = datetime(2003, 1, 1)
    end_date = datetime(2014, 12, 31)
    data = db.extract_data(start_date, end_date, nlat, slat, wlon, elon)
    ddoy = data.groupby(data.index.dayofyear)

    quantiles = [0, 0.1, 0.25, .5, .75, 0.9, 1]
    for p in quantiles:
        d = ddoy.quantile(p)
        d.rename(columns={'sum': p }, inplace=True)
        if quantiles.index(p) == 0:
            ax = d.plot()
        else:
            d.plot(ax=ax)
    # plt.plot(dates, values)

    start_date = datetime(2015, 1, 1)
    end_date = datetime(2015, 10, 31)
    data = db.extract_data(start_date, end_date, nlat, slat, wlon, elon)
    ddoy = data.groupby(data.index.dayofyear)

    d.rename(columns={'sum': '2015' }, inplace=True)
    d.plot(ax=ax)

    plt.savefig("/home/esowc32/PROJECT/DATA/aa.png")
    return data


if __name__ == '__main__':
    d = main()
