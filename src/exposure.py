import numpy as np
import json
import geopandas as gpd
import pandas as pd
import h3
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point

import parameters as prm

from tqdm import tqdm
tqdm.pandas()

###########################
# Définition de fonction (titre naze)
###########################

# --- Convention ---
# Distances are in km
# Ages are in months

def harvesine(lng1, lat1, lng2, lat2):
    # Convert degrees to radians
    lng1 = lng1 * np.pi / 180
    lng2 = lng2 * np.pi / 180
    lat1 = lat1 * np.pi / 180
    lat2 = lat2 * np.pi / 180

    r = 6371 # Earth radius in kilometers
    a = np.sin((lat2 - lat1) / 2)**2
    b = np.cos(lat1) * np.cos(lat2) * np.sin((lng2 - lng1) / 2)**2
    return 2 * r * np.arcsin(np.sqrt(a + b))


def logistic(kappa, gamma, x):
    return 1 / (1 + np.exp(-kappa + gamma*x))


kappa_d = 7
gamma_d = 0.35

def wd(x):
    return logistic(kappa_d, gamma_d, x)

kappa_a = 8
gamma_a = 2.5/30 # On divise par 30 parce que x sera en jours (et pas en mois)

def wa(x):
    return logistic(kappa_a, gamma_a, x)


def wcas(mean, x):
    # Paramètres à discuter
    return 1 / (1 + np.exp(-0.5*(x-mean)))


###########################
# Cadrillage d'un pays
###########################

# GeoJSON : https://geojson-maps.ash.ms/

def swap_lng_lat(geoJSON_Polygon):
    # Les coordonnées des points du geoJSON sont dans l'ordre (lng, lat)
    # mais h3.polyfills() prend des coordonnées dans l'ordre (lat, lng).
    # Il faut donc les échanger dans le JSON.
    geoJSON_Polygon['coordinates'][0] = [[coord[1], coord[0]] for coord in geoJSON_Polygon['coordinates'][0]]


def json_to_h3(country, res):
    """
    Remplit une surface avec des hexagones.

    Parameters
    ----------
    fObj : TextIOWrapper
        Un fichier ouvert avec open()
    res : int
        Résolution H3, entre 1 et 16

    Returns
    -------
    Liste des identifiants des cellules H3 remplissant la surface.
    """
    path = f"../GeoJSONs/{country}.geo.json"
    fObj = open(path)

    s = json.load(fObj)
    s = s['features'][0]['geometry']
    swap_lng_lat(s)
    return h3.polyfill(s, res = res)


def add_geometry(row):
    points = h3.h3_to_geo_boundary(row['h3'], True)
    return Polygon(points)


def country_grid(country, res):
    """
    Crée un GeoDataFrame contenant les Polygons de toutes les cellules remplissant le pays.
    """
    h3 = json_to_h3(country, res)

    df = pd.DataFrame(h3, columns = ['h3'])

    df['geometry'] = df.apply(add_geometry, axis=1)
    
    return gpd.GeoDataFrame(df, crs='EPSG:4326')


def plot_grid(country, res):
    gdf = country_grid(country, res)

    # Plot with borders
    
    ax = gdf.plot(markersize=.1, figsize=(12, 8))
    plt.autoscale(False)
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    world.to_crs(gdf.crs).plot(ax=ax, color='none', edgecolor='black')


###########################
# Exposure calculation
###########################

# On va prendre une h3-résolution de 6, et au lieu de calculer
# les distances de chaque cellule à chaque évènement (et faire
# ainsi exploser l'ordi), on va se contenter de considérer, pour
# chaque cellule, les évènements situés dans les cellules voisines, 
# ainsi que dans les cellules voisines des cellules voisines. 
# 
# Pourquoi faire comme ça ? Parce que le module h3 est optimisé pour
# que ce genre de calcul se fasse rapidement.
#
# Remarque : on peut aussi faire avec des distances 
# (voir https://h3geo.org/docs/api/traversal#kringdistances)
#
# https://rechneronline.de/pi/hexagon.php


def calc_distances(cells, events):
    distances = pd.DataFrame(index=events.index)
    distances['h3'] = events['h3'].copy()

    def calc_event_distance(origin, row):
        cell_lat, cell_lng = h3.h3_to_geo(origin)
        ev_lat, ev_lng = row['latitude'], row['longitude']
        return harvesine(cell_lng, cell_lat, ev_lng, ev_lat)


    for cell in cells:
        ring = h3.k_ring(cell, 2)
        c_events = events.loc[(events['h3'].isin(ring))].copy()

        c_events['distance'] = c_events.apply(lambda row: calc_event_distance(cell, row), axis = 1, result_type='reduce')
        c_events['wd'] = c_events.apply(lambda row: wd(row['distance']), axis = 1, result_type='reduce')
       
       #distances[cell] = c_events['distance']

        distances[cell] = c_events['wd']

    return distances.drop('h3', axis=1)


def cell_exposure_at_t(events, attack_type, origin, date, distances):
    """
    Calcule l'exposition à date de la cellule origin aux events de type attack_type.
    """
    
    ring = h3.k_ring(origin, 2)
    c_events = events.loc[(events['h3'].isin(ring)) & (events['type'] == attack_type)].copy() # On copie https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy

    # Calculate wa

    def calc_event_age(row):
        return date -row['date_start']

    def calc_wa(row):
        if row['age'].days < 0:
            # L'évènement n'a pas encore eu lieu, on ne le prend pas en compte
            return 0

        return wa(row['age'].days)

    c_events['age'] = c_events.apply(calc_event_age, axis = 1, result_type='reduce')
    c_events['wa'] = c_events.apply(calc_wa, axis = 1, result_type='reduce')

    wd_df = distances[origin].loc[(events['h3'].isin(ring)) & (events['type'] == attack_type)]

    return np.dot(wd_df, c_events['wa'])


def get_exposure(events, attack_type, p: prm.Parameters, freq):
    """
    Calcule la matrice d'exposition des cellules des pays listés dans p.
    aux évènements de type attack_type.

    Parameters
    ----------
    events : DataFrame
        Les évènements retenus.
    attack_type : "conventional" ou "terrorism
        Le type d'évènement à isoler.
    p : precleaning.Parameters
        Les paramètres retenus pour la construction de events.
    freq : str or DateOffset, default ‘D’
        frequency string

    Returns
    -------
    exposure : DataFrame
        * En ligne : les cellules
        * En colonne : les dates
    """

    cells = []
    for country in p.countries:
        cells += list(json_to_h3(country, p.h3_level))

    date_range = pd.date_range(p.startdate, p.enddate, freq=freq)

    exposure = pd.DataFrame(data = [[(h3, date) for date in date_range] for h3 in cells],
                            index = cells,
                            columns = date_range)

    distances = calc_distances(cells, events)

    def calc_exposure(c):
        origin, date = c[0], c[1]
        return cell_exposure_at_t(events, attack_type, origin, date, distances)

    return exposure.progress_applymap(calc_exposure)


def fast_get_exposure(events, attack_type, params: prm.Parameters, freq):
    # Peut-être plus rapide avec numpy
    cells = []
    for country in params.countries:
        cells += list(json_to_h3(country, params.h3_level))

    date_range = pd.date_range(params.startdate, params.enddate, freq=freq)

    distances = calc_distances(cells, events)

    exposure = np.array([[cell_exposure_at_t(events, attack_type, origin, date, distances) for date in date_range] for origin in cells])

    return pd.DataFrame(data=exposure, index=cells, columns=date_range)


def cell_exposure_at_t_with_cas(events, attack_type, origin, date, distances):
    """
    Calcule l'exposition à date de la cellule origin aux events de type attack_type
    en prenant en compte le nombre de victimes ("cas" = casualties).
    """
    
    ring = h3.k_ring(origin, 2)
    c_events = events.loc[(events['h3'].isin(ring)) & (events['type'] == attack_type)].copy() # On copie https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy

    # Calculate wa

    def calc_event_age(row):
        return date -row['date_start']

    def calc_wa(row):
        if row['age'].days < 0:
            # L'évènement n'a pas encore eu lieu, on ne le prend pas en compte
            return 0

        return wa(row['age'].days)

    c_events['age'] = c_events.apply(calc_event_age, axis = 1, result_type='reduce')
    c_events['wa'] = c_events.apply(calc_wa, axis = 1, result_type='reduce')

    # Fetch wd

    wd_df = distances[origin].loc[(events['h3'].isin(ring)) & (events['type'] == attack_type)]

    # Calculate wcas

    def calc_wcas(row):
        # On regarde le nombre moyen de victimes sur les trois derniers mois
        recent_events = c_events.loc[(c_events['age'].dt.days >= 0) & (c_events['age'].dt.days <= 90)]
        mean = recent_events['fatalities'].mean()
        return wcas(mean, row['fatalities'])

    c_events['wcas'] = c_events.apply(calc_wcas, axis = 1, result_type='reduce')
    c_events.fillna(c_events['wcas'].mean(), inplace=True)
    
    return np.dot(wd_df, c_events['wa'] * c_events['wcas'])


def get_exposure_with_cas(events, attack_type, p: prm.Parameters, freq):
    """
    Calcule la matrice d'exposition des cellules des pays listés dans p.
    aux évènements de type attack_type, en prenant en compte le nombre de victimes.
    """

    cells = []
    for country in p.countries:
        cells += list(json_to_h3(country, p.h3_level))

    date_range = pd.date_range(p.startdate, p.enddate, freq=freq)

    exposure = pd.DataFrame(data = [[(h3, date) for date in date_range] for h3 in cells],
                            index = cells,
                            columns = date_range)

    distances = calc_distances(cells, events)

    def calc_exposure(c):
        origin, date = c[0], c[1]
        return cell_exposure_at_t_with_cas(events, attack_type, origin, date, distances)

    return exposure.progress_applymap(calc_exposure)


def plot_exposure(exposure, date):
    # Cette fonction est à bidouiller à la main pour chaque matrice exposure

    events = pd.DataFrame(exposure.loc[:, date].copy())
    events['geometry'] = events.apply(lambda row: Polygon(h3.h3_to_geo_boundary(row.name, True)), axis=1)
    events.columns = ['exposure', 'geometry']
    
    events = gpd.GeoDataFrame(events, crs='EPSG:4326')

    vmin, vmax = 0, exposure.max().max()

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
    ax.set_title(f'Conventional warfare in Syria in {date.year}')

    # C'est une horrible manière de faire, mais je n'ai pas le temps de réfléchir
    months=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    ax.annotate(months[date.month - 1],
                xy=(0.5, .3), xycoords='figure fraction',
                horizontalalignment='left', verticalalignment='top',
                fontsize=16)


###########################
# Main execution
###########################


def main():
    import precleaning as pcl

    p = prm.ask_params()
    startdate, enddate, countries, perpetrators, h3_level, freq = p.get_params()

    def choose_attack():
        exposure = input("Choose attack type : [t]errorism, [c]onventional > ")
        if exposure == "t":
            return "terrorism"
        elif exposure == "c":
            return "conventional"
        else:
            return choose_attack()
   
    attack_type = choose_attack()

    events = pcl.get_events(p)
    
    E = get_exposure(events, attack_type, p, freq)

    def str_countries(countries):
        res = str(countries[0])
        for i in range(1, len(countries)):
            res += "-" + str(countries[i])
        return res

    E.to_csv(f"../exposures/exposure_{str_countries(countries)}_{attack_type}_{startdate}_{enddate}_{freq}.csv")


def time_comparaison():
    import precleaning as pcl
    import time

    p = prm.ask_params()
    startdate, enddate, countries, perpetrators, h3_level, freq = p.get_params()

    def choose_attack():
        exposure = input("Choose attack type : [t]errorism, [c]onventional > ")
        if exposure == "t":
            return "terrorism"
        elif exposure == "c":
            return "conventional"
        else:
            return choose_attack()
   
    attack_type = choose_attack()

    events = pcl.get_events(p)
    events.index = [i for i in range(len(events.index))]

    E = get_exposure(events, attack_type, p, freq)
    
    t = time.perf_counter()
    F = fast_get_exposure(events, attack_type, p, freq)
    print("Fast exposure: ", time.perf_counter()-t)

if __name__ == "__main__":
    main()
    # time_comparaison()




# Test variables

# origin = '862c16b1fffffff' # Mossoul
# startdate = params.startdate
# enddate = params.enddate
# date_range = pd.date_range(startdate, enddate, freq='M')
# date = date_range[5]
