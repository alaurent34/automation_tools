import os
os.environ['USE_PYGEOS'] = '0'
import argparse
import shutil
import sys
import json

import pandas as pd
import geopandas as gpd

GEOBASE_PATH = 'https://donnees.montreal.ca/dataset/88493b16-220f-4709-b57b-1ea57c5ba405/resource/16f7fa0a-9ce6-4b29-a7fc-00842c593927/download/gbdouble.json'

PERIODS_HR = {
    'Matin':[6, 12],
    'Après-midi et soir':[13, 23]
}

PERIODS_DAY = {
   'all':[0,6]
   # 'week_end':[5,6],
   # 'week_day':[0,4]
}


def parse_args() -> argparse.Namespace:
    """
    Argument parser for the script

    Return
    ------
    argparse.Namespace
        Parsed command line arguments
    """
    # Initialize parser
    parser = argparse.ArgumentParser(
            description="This script provide an automation to export plaque data" +
                        " to SAAQ standard."
            )

    # Adding optional argument
    parser.add_argument("plaque", metavar='Data path', type=str,
                        help="Path to the plaque data.")
    parser.add_argument("zone", metavar='Zone', type=str,
                        help="Path of the GeoJSON boundary " +
                        "of the studied SAAQ zone.")
    parser.add_argument("--gdbl-path", default=GEOBASE_PATH,
                        dest='geobase_path',
                        help="Path to custom geobase.")
    parser.add_argument("--period-hr", default=PERIODS_HR, type=json.loads,
                        dest='periods_hr',
                        help="Specify analysis periods hours as a json array. Format:"\
                        +"'{<period_name>: [hr_deb, hour_end]}'")
    parser.add_argument("--period-day", default=PERIODS_DAY, type=json.loads,
                        dest='periods_day',
                        help="Specify analysis periods day as a json array. Format:"\
                        +"{<period_name>:[day_integer_i, ...]}")
    parser.add_argument("--zone-name", default='Nom',
                        dest='zone_name',
                        help="Specify zone name")
    # Read arguments from command line
    args = parser.parse_args()

    return args

def parse_time_period(period_array):
    """ Get a human readable period array and convert it
    project readable object.

    Parameter
    ---------
    array

    """
    parsed_periods = {}
    for period, hour_interval in period_array.items():
        for hour in range(hour_interval[0], hour_interval[-1]+1, 1):
            parsed_periods[hour] = period

    return parsed_periods

def create_dir(dir_name):
    """
    """
    # save
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name, ignore_errors=False)
    os.makedirs(dir_name, exist_ok=True)


def export_data(data, dir_name, zone_name):
    """
    """
    data = data.copy()

    create_dir(dir_name)

    # re-index
    data = data[['plaque', zone_name, 'period', 'day']]
    data = data.drop_duplicates(keep='first').reset_index(drop=True)

    for (zone, period, day), df in data.groupby([zone_name, 'period', 'day']):
        df = df.reset_index().rename(
            columns = {
                'index':'Champ2',
                'plaque':'NO_PLAQ'
            }
        )
        df[['Champ2', 'NO_PLAQ']].to_excel(
            f'export/Plaques_zone_{zone}_periode_{period}_{day}.xlsx',
            index=False
        )


def main():
    """TODO: Docstring for main.
    """
    # parse project args
    config = parse_args()

    # periods
    periods_hr = parse_time_period(config.periods_hr)
    periods_day = parse_time_period(config.periods_day)

    # load data
    zones = gpd.read_file(config.zone).to_crs('epsg:32188')
    geobase = gpd.read_file(config.geobase_path).to_crs('epsg:32188')
    data = pd.read_csv(config.plaque)

    # Recover Geobase for the zone
    geobase_zone = gpd.sjoin(geobase, zones, predicate='within', how='inner')
    geobase_zone = geobase_zone[['ID_TRC', 'NOM_VOIE', 'geometry', config.zone_name]].reset_index()

    # filter plaque by zone
    data_filtered = pd.merge(data, geobase_zone, left_on='segment', right_on='ID_TRC', how='inner')

    # compute periods
    data_filtered['datetime'] = pd.to_datetime(data_filtered['datetime'])
    data_filtered['period']   = data_filtered.datetime.dt.hour.map(periods_hr)
    data_filtered['day']      = data_filtered.datetime.dt.day_of_week.map(periods_day)

    # export
    export_data(data_filtered, 'export', config.zone_name)


if __name__ == '__main__':
    main()
