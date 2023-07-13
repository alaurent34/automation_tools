"""
File: compute_mean_parking_spot.py
Author: Antoine Laurent
Email: alaurent@agencemobilitedurable.ca
Github: https://github.com/alaurent34
Description: Script to compute the mean number of available parking spot per
street.
"""

import argparse
import os
os.environ['USE_PYGEOS'] = '0'
import itertools
import json
from typing import List
from unidecode import unidecode
import sys
import pandas as pd
import geopandas as gpd
from querry_bunch_projects import slugify
from lapin.analysis.restrictions import RestrictionHandler

# ASSET CONFIG
GEOBASE_PATH = os.path.join(os.path.dirname(__file__),
                            'assets/geobase_simple.geojson')
GEOBASE_IDX_COL = 'ID_TRC'


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
            description="This script provide an automation to batch querry" +
                        " projects from the capacity app."
            )

    # Adding optional argument
    parser.add_argument("projects_list", metavar='Project list', type=str,
                        nargs='*', default=[],
                        help="List of project names to querry.")
    # Read arguments from command line
    args = parser.parse_args()

    if not sys.stdin.isatty():
        args.projects_list.extend(sys.stdin.read().splitlines())

    return args


def read_json_file(path: str) -> dict:
    """TODO: Docstring for read_file.

    :arg1: TODO
    :returns: TODO
    """
    with open(path, 'r') as f:
        data = json.load(f)

    return data


def merge_capacities(capacities_list: List) -> dict:
    """TODO: Docstring for merge_capacities.

    :capacities_list: List of capacity objects
    :returns: TODO

    """
    return list(itertools.chain(*capacities_list))


def save_capacity(restrict_h):
    """TODO: Docstring for save_capacity.
    :returns: TODO

    """
    restrict = pd.concat([restrict_h.seg_base, restrict_h.seg_info])
    restrict.to_csv('./output/segments_capacity.csv')

    capa = restrict_h.get_capacity(time_period='all')
    capa.to_csv('./output/capacity_all_time.csv')


def main():
    """TODO: Docstring for main.
    :returns: TODO

    """
    config = parse_args()

    projects = config.projects_list

    capacities = map(
        read_json_file,
        ['./output/'+slugify(unidecode(project))+'_capacity_array.json'
         for project in projects]
    )

    merge_capa = merge_capacities(capacities)

    geobase = gpd.read_file(GEOBASE_PATH)

    id_trc = pd.DataFrame.from_dict(merge_capa)['properties'].apply(
        lambda x: x.get('id_trc')
    ).values
    geobase = geobase[geobase[GEOBASE_IDX_COL].isin(id_trc)]

    restrict_h = RestrictionHandler.from_json(merge_capa, geobase,
                                              geobase_idx=GEOBASE_IDX_COL)

    save_capacity(restrict_h)


if __name__ == "__main__":
    main()
