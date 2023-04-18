import numpy as np, pandas as pd, json, h3, geopandas, matplotlib.pyplot as plt, parameters as prm
from numba import njit
from shapely.geometry import Polygon, Point


########################
# Cadrillage d'un pays #
########################

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
    country : str
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


###########################
# Calcule de l'exposition #
###########################


@njit
def harvesine(lng1, lat1, lng2, lat2):
    """
    Calcule la distance (sur la sphère terrestre) entre deux points.
    """
    # Convert degrees to radians
    lng1 = lng1 * np.pi / 180
    lng2 = lng2 * np.pi / 180
    lat1 = lat1 * np.pi / 180
    lat2 = lat2 * np.pi / 180

    r = 6371 # Earth radius in kilometers
    a = np.sin((lat2 - lat1) / 2)**2
    b = np.cos(lat1) * np.cos(lat2) * np.sin((lng2 - lng1) / 2)**2
    return 2 * r * np.arcsin(np.sqrt(a + b))

@njit
def calc_distances(cells_coord, events_coord, is_in_ring):
    """
    Calcule la matrice de distance cellules-évènements.
    """
    res = np.zeros((len(cells_coord), len(events_coord)), dtype='float64')
    for i in range(len(cells_coord)):
        for j in range(len(events_coord)):
            if is_in_ring[i,j]: # if events_coord[j] is in ring(cells_coord[i])
                lat1, lng1 = cells_coord[i][0], cells_coord[i][1]
                lat2, lng2 = events_coord[j][0], events_coord[j][1]
                res[i,j] = harvesine(lng1, lat1, lng2, lat2)

    return res

# ------------------------------------------------------------------------

@njit
def logistic(kappa, gamma, x):
    return 1 / (1 + np.exp(-kappa + gamma*x))

kappa_d = 7
gamma_d = 0.35

@njit
def wd(x):
    return logistic(kappa_d, gamma_d, x)

kappa_a = 8
gamma_a = 2.5 / 2592000 # On divise par 2592000 = nb de secondes dans un 30 jours parce que x sera en secondes

@njit
def wa(x):
    if x < 0:
        # L'évènement n'a pas encore eu lieu, on ne le prend pas en compte
        return 0
    else:
        return logistic(kappa_a, gamma_a, x)

# ------------------------------------------------------------------------

@njit
def cell_exposure_at_t(events_dates, cell_index, date, is_in_ring, distances):
    """
    Calcule l'exposition d'une cellule à une date donnée.
    """
    n_events = is_in_ring.shape[1]

    wa_array = np.zeros(n_events, dtype='float64')
    wd_array = np.zeros(n_events, dtype='float64')

    for j in range(n_events):
        if is_in_ring[cell_index, j]:
            age = date - events_dates[j]
            wa_array[j] = wa(age)
            wd_array[j] = wd(distances[cell_index, j])

    return np.dot(wd_array, wa_array)

def get_exposure_raw(events_dates, is_in_ring, distances, date_range):
    """
    Calcule un tableau numpy d'exposition des cellules sur une période.
    "raw" car get_exposure est déjà pris.
    """

    n_cells, n_events = distances.shape
    n_dates = len(date_range)
    exposure = np.zeros((n_cells, n_dates), dtype='float64')

    for i in range(n_cells):
        for d in range(n_dates):
            exposure[i][d] = cell_exposure_at_t(events_dates, i, date_range[d], is_in_ring, distances)

    return exposure

# ------------------------------------------------------------------------

# Il faut faire le lien entre les "fonctions Numba" ci-dessus
# et le design de code de exposure.py

def get_exposure(events, attack_type, p, freq):
    """
    """

    cells = []
    for country in p.countries:
        cells += list(json_to_h3(country, p.h3_level))

    cells_coord = np.array([[h3.h3_to_geo(c)[0], h3.h3_to_geo(c)[1]] for c in cells], dtype='float64')
    events_of_type = events[events["type"] == attack_type]
    events_coord = events_of_type[["latitude", "longitude"]].to_numpy(dtype='float64')

    events_h3 = events_of_type["h3"].to_numpy()
    rings = np.array([list(h3.k_ring(str(cell), 2)) for cell in cells], dtype='object')
    is_in_ring = np.array([np.isin(events_h3, ring) for ring in rings])

    date_range = pd.date_range(p.startdate, p.enddate, freq=freq)
    date_range = ((date_range - pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")).to_numpy()

    events_dates = ((events["date_start"] - pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")).to_numpy()

    distances = calc_distances(cells_coord, events_coord, is_in_ring)

    g = get_exposure_raw(events_dates, is_in_ring, distances, date_range)

    return pd.DataFrame(g, index=cells, columns=pd.to_datetime(date_range, unit="s"))

# ------------------------------------------------------------------------

def main():
    import precleaning as pcl
    import time

    p = prm.ask_params()
    startdate, enddate, countries, _, _, freq = p.get_params()

    def choose_attack():
        exposure = input("Choose attack type : [t]errorism | [c]onventional > ")
        if exposure == "t":
            return "terrorism"
        elif exposure == "c":
            return "conventional"
        else:
            return choose_attack()
   
    attack_type = choose_attack()

    events = pcl.get_events(p)
    
    t = time.perf_counter()
    E = get_exposure(events, attack_type, p, freq)
    t = time.perf_counter() - t

    print(f"Exposure computed in {t} seconds.\n")
    print(E)

    def str_countries(countries):
        res = str(countries[0])
        for i in range(1, len(countries)):
            res += "-" + str(countries[i])
        return res

    # On enregistre le résultat
    save = (input("Save ? y/N > ") == "y") or False
    if save:
        E.to_csv(f"../exposures/exposure-numba_{str_countries(countries)}_{attack_type}_{startdate}_{enddate}_{freq}.csv")

if __name__ == "__main__":
    main()
