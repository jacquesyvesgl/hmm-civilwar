import pandas as pd
import numpy as np
import h3
import parameters as prm


###########################
# GED data precleaning
###########################

def get_ged_df(path):
    """
    Charge la base de donnée GED et sélectionne les variables utiles.
    """
    ged_dtype = {'year': int,
                 'type_of_violence' : int,
                 'side_a' : str,
                 'side_b' : str,
                 'source_article' : str,
                 'source_headline' : str,
                 'where_prec' : int,
                 'latitude' : float,
                 'longitude' : float,
                 'geom_wkt' : str, # A préciser peut-être ?
                 'priogrid_gid' : int,
                 'country' : str,
                 'date_prec' : int,
                 'date_start' : str,
                 'date_end' : str,
                 'deaths_a' : int,
                 'death_b' : int,
                 'deaths_civilians' : int,
                 'deaths_unknown' : int,
                 'best' : int,
                 'high' : int,
                 'low' : int}

    ged = pd.read_csv(path, dtype = ged_dtype) 

    ged['date_start'] = pd.to_datetime(ged['date_start'])
    ged['date_end'] = pd.to_datetime(ged['date_end'])
    ged['extended'] = ged['date_start'] != ged['date_end']
    ged['type'] = "conventional"
    ged['day'] = ged['date_start'].dt.day
    ged['month'] = ged['date_start'].dt.month
    ged['year'] = ged['date_start'].dt.year
    ged['duration'] = ged['date_end'] - ged['date_start'] + pd.Timedelta("1 days")

    # Selecting relevant observations
    # a) state-based conflict. In state-based armed conflicts, at least one of the primary parties must be the government of a state.
    # b) not attributable to min 2nd order admin region

    ged = ged[ged['type_of_violence'] == 1 & ged['where_prec'].isin([1, 2, 3])]

    # Select relevant variables

    ged = ged[[
        'year',
        'month', 
        'day', 
        'date_start',
        'date_end',
        'date_prec',
        'extended',
        'duration',
        'country',
        'longitude',
        'latitude',
        'where_prec',
        'best',
        'side_b',
        'type',
        'type_of_violence',
    ]]

    ged = ged.rename(columns = {
        'where_prec' : 'prec_tax',
        'best' : 'fatalities',
        'side_b' : 'perpetrator',
        'type_of_violence' : 'event_tax',
    })

    return ged


###########################
# GTD data precleaning
###########################

def get_gtd_df(path):
    """
    Charge la base de donnée GTd et sélectionne les variables utiles.
    """    
    gtd_dtype = {'iyear' : int,
                 'imonth' : int,
                 'iday' : int,
                 'extended' : int,
                 'country_txt' : str,
                 'latitude' : float,
                 'longitude' : float,
                 'specificity' : int,
                 'summary' : str,
                 'doutterr' : int,
                 'alternative' : int,
                 'multiple' : int,
                 'success' : int,
                 'attacktype1' : int,
                 'attacktype_txt' : str,
                 'targtype1' : int,
                 'targtype1_txt' : str,
                 'targsubtype1' : int,
                 'targsubtype1_txt' : str,
                 'gname' : str,
                 'weaptype1' : int,
                 'weaptype1_txt' : str,
                 'weapsubtype1' : int,
                 'weapsubtupe1_txt' : str,
                 'nkill' : int,
                 'nwound' : int}

    gtd = pd.read_csv(path)

    # Rename columns
    gtd.rename(columns = {
        'iyear' : 'year',
        'imonth' : 'month',
        'iday' : 'day'
    }, inplace = True)

    # Set 0 day/month value to 1 for conversion to Timestamp
    gtd.loc[gtd['day'] == 0, 'day'] = 1
    gtd.loc[gtd['month'] == 0, 'month'] = 1

    #gtd['doubtterr'] = gtd['doubtterr'].replace(-9, np.NaN)
    gtd['date_start'] = pd.to_datetime(gtd[['year', 'month', 'day']])
    gtd['date_end'] = pd.to_datetime(gtd['resolution'])
    gtd['duration'] = gtd['date_end'] - gtd['date_start'] + pd.Timedelta("1 days")
    gtd['type'] = "terrorism"
    gtd.loc[gtd['extended'] == 0, 'duration'] = pd.Timedelta("1 days")

    # Coding a time precision variable
    def calc_date_prec(row):
        # Y a peut-être plus simple comme écriture, mais bon.
        date_prec = np.NaN
        if row['approxdate'] == "":
            date_prec = 1
        else:
            date_prec = 2
        if row['month'] != 0 and row['day'] == 0:
            date_prec = 3
        if row['month'] == 0:
            date_prec = 5

        return date_prec

    gtd['date_prec'] = gtd.apply(calc_date_prec, axis = 1)

    # Filtering out events 
    # a) not clearly terrorism
    # b) not attributable to min 2nd order admin region
    # c) Main model: removing attacks against military

    gtd = gtd[(gtd['targtype1'] != 4) & (gtd['doubtterr'] == 0) & gtd['specificity'].isin([1, 2, 3])]

    # Select relevant variables

    gtd = gtd[[
        'year',
        'month',
        'day',
        'date_start',
        'date_end',
        'date_prec',
        'extended',
        'duration',
        'country_txt',
        'longitude',
        'latitude',
        'specificity',
        'nkill',
        'gname',
        'type',
        'attacktype1',
        'doubtterr',
        'targtype1',
        'attacktype1_txt'
    ]]

    gtd.rename(columns = {
        'country_txt' : 'country',
        'specificity' : 'prec_tax',
        'nkill' : 'fatalities',
        'gname' : 'perpetrator',
        'attacktype1' : 'event_tax',
    }, inplace = True)

    return gtd


###########################
# Data selection
###########################

def select(ged, gtd, startdate, enddate, countries, perpetrators):
    """
    Filtre les bases GED et GTD, puis les fusionne.
    """
    # perpetrators n'est pas utilisé, pour l'instant.

    ged_select_col = ged[(startdate <= ged['date_start']) & (ged['date_start'] <= enddate) & ged['country'].isin(countries)]
    gtd_select_col = gtd[(startdate <= gtd['date_start']) & (gtd['date_start'] <= enddate) & gtd['country'].isin(countries)]

    return pd.concat([gtd_select_col, ged_select_col])


###########################
# Hexagonal grid
###########################

def grid(df, h3_level):
    """
    Ajoute les cellules H3.
    """
    def lat_lng_to_h3(row):
        return h3.geo_to_h3(row.latitude, row.longitude, h3_level)
    
    df['h3'] = df.apply(lat_lng_to_h3, axis = 1)


###########################
# Et hop ça part dans la boite
###########################

def get_events(p: prm.Parameters):
    """
    Renvoie une DataFrame contenant l'ensemble des évènements
    parmi les bases GED et GTD correspondants aux paramètres p.
    """
    
    ged = get_ged_df(p.ged_path)
    gtd = get_gtd_df(p.gtd_path)

    df = select(ged, gtd, p.startdate, p.enddate, p.countries, p.perpetrators)
    grid(df, p.h3_level)

    return df


def main():
    p = prm.ask_params()

    df = get_events(p)
    print(df)

if __name__ == "__main__":
    main()
