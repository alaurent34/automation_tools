# -*- coding: utf-8 -*-
"""
File: create_project.py
Author: Antoine Laurent, Laurent Gauthier
Email: alaurent@agencemobilitedurable.ca, lgauthier@agencemobilitedurable.ca
Github: https://github.com/alaurent34
Description:

Helper tool to create and push a capacity project onto the web app.

Usage :
    create_project <ProjectName> <SecteurZonePath>
"""

# Python program to demonstrate
# command line arguments
import os
import sys
import argparse
import datetime
import requests
import logging as log
import pandas as pd
os.environ['USE_PYGEOS'] = '0'
import geopandas as gpd

# ASSET CONFIG
GEOBASE_PATH = os.path.join(os.path.dirname(__file__),
                            'assets/geodouble_2950.geojson')
GEOBASE_IDX_COL = 'COTE_RUE_ID'

# APP CONFIG
APP_URL = ""

# DEFAULT ZONE NAME
SECTOR_NAME = 'NomSecteur'

# UTILS
DATE = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def parse_args():
    """
    Argument parser for the script
    """
    # Initialize parser
    parser = argparse.ArgumentParser(
            description="This script provide an automation to upload project" +
                        " to the capacity app."
            )

    # Adding optional argument
    parser.add_argument("project_name", metavar='Project name', type=str,
                        help="Name of the project.")
    parser.add_argument("zone", metavar='Zone', type=str,
                        help="Path of the GeoJSON boundary " +
                        "of the studied zone.")
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        dest='verbose_count')
    parser.add_argument("--desc", default="", dest='project_desc',
                        help="Description for the project")
    parser.add_argument("--zone-id", default=SECTOR_NAME, dest='zone_id',
                        help="Id used in the GeoJSON file to address" +
                             "the zone, default: "+GEOBASE_IDX_COL)
    parser.add_argument("--gdbl-path", default=GEOBASE_PATH,
                        dest='geobase_path',
                        help="Path to custom geobase.")
    parser.add_argument("--gbdl-id", default=GEOBASE_IDX_COL,
                        dest='geobase_id',
                        help="Custom ID for geobase.")
    parser.add_argument("--merge-sect", default=False, dest='merge_sect',
                        help="Put all sectors in the same project.")

    # Read arguments from command line
    args = parser.parse_args()

    return args


def set_verbose_level(level: int):
    """
    Set verbose level

    Parameters
    ----------
    level: int
        level of verbose
    """
    if level > 0:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.INFO)
        log.info("Verbose output.")
    else:
        log.basicConfig(format="%(levelname)s: %(message)s")


def assure_same_crs(gdf1, gdf2):
    """ Enforce crs of gdf2 to the same CRS as gdf1.

    Parameters
    ----------
    gdf1: geopandas.GeoDataFrame
        First geometric collection
    gdf2: geopandas.GeoDataFrame
        Second geometry collection

    Returns
    -------
    geopandas.GeoDataFrame
        gdf2 with gdf1 crs

    """
    assert isinstance(gdf1, gpd.GeoDataFrame),\
           'First argument is not a GeoDataFrame'

    assert isinstance(gdf2, gpd.GeoDataFrame),\
           'Second argument is not a GeoDataFrame'

    assert gdf1.crs, "CRS of first geometry should not be None"
    assert gdf2.crs, "CRS of second geometry should not be None"

    if gdf1.crs != gdf2.crs:
        gdf2 = gdf2.to_crs(gdf1.crs)

    return gdf2


def clean_columns_names(df, suffix):
    """
    Add suffix to all columns names.

    Parameters
    ----------
    df: pd.DataFrame
        Data.
    suffix: str
        Suffix to append to all column names.

    Returns
    -------
    pd.DataFrame
        Data with renamed columns
    """
    names = {
        x: x.lower()+f'_{suffix.lower()}' if x.lower() == 'id' else x.lower()
        for x in df.columns
    }
    return df.rename(columns=names)


def clean_doublons(frame, index_by=GEOBASE_IDX_COL.lower()):
    """
    doc
    """
    return frame.groupby(index_by).nth(0).reset_index()


def upload(app_url: str, project_name: str, road_list: str,
           description: str = None):
    """
    doc
    """
    payload = {
            'name': project_name,
            'description': description,
            'geobaseIds': road_list,
    }

    response = requests.post(app_url, json=payload)

    if response.status_code == 200:
        log.info(project_name, 'Upload successfull')
    else:
        print('There has been an error. Status : ', response.status_code)
        log.info(response.text)


def gen_outputs(path: str, names: str, frame: pd.DataFrame,
                sector_id: str = SECTOR_NAME, road_id: str = GEOBASE_IDX_COL):
    """
    doc
    """

    frame.to_file(os.path.join(path, names+".geojson"),
                  index=False, driver='GeoJSON')

    for sector, data in frame.groupby(sector_id.lower()):
        with open(os.path.join(path, path,
                               names + sector + "_asList.txt"),
                  'w') as f:
            f.write(
                ",\n".join([str(i) for i in data[road_id.lower()].tolist()])
            )


def main():

    config = parse_args()

    # set log
    set_verbose_level(config.verbose_count)

    # read files
    zone = gpd.read_file(config.zone)
    geobase = gpd.read_file(config.geobase_path)

    zone = assure_same_crs(geobase, zone)

    # clip roads into zone
    roads_cut = gpd.sjoin(clean_columns_names(geobase, 'geodbl'),
                          clean_columns_names(zone, 'zoneetude'),
                          predicate='within')

    roads_cut = clean_doublons(roads_cut,
                               index_by=config.geobase_id.lower())

    # Each sub-secteur have one capacity project unless specified
    # otherwise by user imput.
    if config.merge_sect:
        road_list = [int(i) for i in roads_cut[config.geobase_id.lower()].tolist()]

        upload(
            app_url=APP_URL,
            project_name=config.project_name,
            road_list=road_list,
            description=config.project_desc
        )
        sys.exit(0)

    for sector, sector_roads in roads_cut.groupby(config.zone_id.lower()):
        road_list = [int(i) for i in sector_roads[config.geobase_id.lower()].tolist()]

        upload(
            app_url=APP_URL,
            project_name=config.project_name + " - " + str(sector),
            road_list=road_list,
            description=config.project_desc
        )

    sys.exit(0)

if __name__ == "__main__":
    main()
