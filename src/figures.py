import numpy as np
import geopandas as gpd
import pandas as pd
import h3
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point

# val_map = {'R':1, 'DR':0.75, 'D':0.5, 'DG':0.25, 'G':0}
val_map = {'R':0, 'DR':0.25, 'D':0.5, 'DG':0.75, 'G':1}


def add_geometry(row):
    points = h3.h3_to_geo_boundary(row.name, True)
    return Polygon(points)

#------------------------------
# Control plotting
#------------------------------

def to_gdf(states_df):
    states_gdf = states_df.copy()

    for c in states_gdf.columns:
        states_gdf[c] = states_gdf[c].apply(lambda x: val_map[x])

    states_gdf['geometry'] = states_df.apply(add_geometry, axis=1)

    return gpd.GeoDataFrame(states_gdf, crs='EPSG:4326')


def plot_control(states_gdf, country):
    # Fonction écrite en freestyle

    months=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

    for c in states_gdf.columns[:-1]:
        _, ax = plt.subplots(1, 1)
        df = pd.DataFrame(states_gdf.loc[:, [c, 'geometry']].copy())
        df.columns = ['control', 'geometry']

        df = gpd.GeoDataFrame(df, crs='EPSG:4326')

        df.plot(column='control',
                ax=ax,
                cmap='viridis',
                figsize=(10,10),
                vmin=0., vmax=1.,
                legend=True,
                norm=plt.Normalize(vmin=0., vmax=1.))

        plt.autoscale(False)
        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
        world.to_crs(df.crs).plot(ax=ax, color='none', edgecolor='black')

        ax.axis('off')
        
        date = pd.Timestamp(c)
        ax.set_title(f'Territorial control in {country} in {date.year}')

        ax.annotate(months[date.month- 1],
                xy=(0.13, .3), xycoords='figure fraction',
                horizontalalignment='left', verticalalignment='top',
                fontsize=16)
        
        plt.savefig(f'../figures/controls_{country}_' + c.strftime('%Y-%m-%d') + '.png')
        plt.close()


#------------------------------
# Exposure plotting
#------------------------------

def plot_exposure(exposure, date, attack_type, country):
    # Cette fonction est à bidouiller à la main pour chaque matrice exposure

    events = pd.DataFrame(exposure.loc[:, date].copy())
    events['geometry'] = events.apply(lambda row: Polygon(h3.h3_to_geo_boundary(row.name, True)), axis=1)
    events.columns = ['exposure', 'geometry']
    
    events = gpd.GeoDataFrame(events, crs='EPSG:4326')

    vmin, vmax = 0, exposure[date].max()

    _, ax = plt.subplots(1, 1)
    events.plot(column='exposure',
                ax=ax,
                cmap='OrRd',
                figsize=(10,10), 
                vmin=vmin, vmax=vmax,
                legend=True,
                norm=plt.Normalize(vmin=vmin, vmax=vmax))

    plt.autoscale(False)
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    world.to_crs(events.crs).plot(ax=ax, color='none', edgecolor='black')

    ax.axis('off')
    ax.set_title(f'{attack_type} warfare in {country} in {date.year}')

    # C'est une horrible manière de faire, mais je n'ai pas le temps de réfléchir
    months=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    ax.annotate(months[date.month - 1],
                xy=(0.5, .3), xycoords='figure fraction',
                horizontalalignment='left', verticalalignment='top',
                fontsize=16)


def main():
    states_df = pd.read_csv("../controls/" + input("Enter exposure filename for control"), index_col=0).T
    states_gdf = to_gdf(states_df)
    plot_control(states_gdf)
