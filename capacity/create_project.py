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
import argparse
import datetime
import logging as log
import requests
import sys
from typing import List
import urllib.request

import pandas as pd
os.environ['USE_PYGEOS'] = '0'
import geopandas as gpd

# ASSET CONFIG
GEOBASE_PATH = 'https://donnees.montreal.ca/dataset/88493b16-220f-4709-b57b-1ea57c5ba405/resource/16f7fa0a-9ce6-4b29-a7fc-00842c593927/download/gbdouble.json'
GEOBASE_IDX_COL = 'COTE_RUE_ID'

# APP CONFIG
APP_URL = ""
API_CREATE = ""
API_CONNECT = ""

# DEFAULT ZONE NAME
SECTOR_NAME = 'NomSecteur'

# UTILS
DATE = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


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
    parser.add_argument('-u', '--user', type=str, default=None,
                        help='User name for Curbsnapp')
    parser.add_argument('-p', '--pwd', type=str, default=None,
                        help='Password for Curbsnapp')
    parser.add_argument('-k', '--api-key', type=str, default=None, help='API key')
    parser.add_argument("--desc", default="", dest='project_desc',
                        help="Description for the project")
    parser.add_argument("--zone-id", default=SECTOR_NAME, dest='zone_id',
                        help="Id used in the GeoJSON file to address" +
                             "the zone, default: "+SECTOR_NAME)
    parser.add_argument("--gdbl-path", default=GEOBASE_PATH,
                        dest='geobase_path',
                        help="Path to custom geobase.")
    parser.add_argument("--gbdl-id", default=GEOBASE_IDX_COL,
                        dest='geobase_id',
                        help="Custom ID for geobase.")
    parser.add_argument("--merge-sect", action="store_true", dest='merge_sect',
                        help="Put all sectors in the same project.")
    parser.add_argument("--print-only", action="store_true", dest='print_only',
                        help="Do not push to app, only print IDs.")

    # Read arguments from command line
    args = parser.parse_args()

    return args


def set_verbose_level(level: int) -> None:
    """
    Set verbose level

    Parameters
    ----------
    level: int
        level of verbose
    """
    if level > 1:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
        log.info("Debug output.")
    elif level > 0:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.INFO)
        log.info("Verbose output.")
    else:
        log.basicConfig(format="%(levelname)s: %(message)s")

def read_mtl_open_data(url: str, encoding : str = 'utf-8') -> gpd.GeoDataFrame:
    """_summary_

    Parameters
    ----------
    url : _type_
        _description_
    encoding : str, optional
        _description_, by default 'utf-8'

    Returns
    -------
    _type_
        _description_
    """
    req = urllib.request.urlopen(url)
    lines = req.readlines()
    if not encoding:
        encoding = req.headers.get_content_charset()
    lines = [line.decode(encoding) for line in lines]
    data = gpd.read_file(''.join(lines))

    return data

def assure_same_crs(gdf1: gpd.GeoDataFrame,
                    gdf2: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
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


def connect(url, user, password) -> requests.Session:

    login_data = {'username': user, 'password': password}

    session = requests.Session()
    session.post(url, data=login_data, timeout=600)

    return session


def clean_columns_names(df: pd.DataFrame, suffix: str) -> pd.DataFrame:
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


def clean_doublons(frame: pd.DataFrame,
                   index_by: str = GEOBASE_IDX_COL.lower()) -> pd.DataFrame:
    """
    Clean doublons in column <index_by>.

    Parameters
    ----------
    frame: pandas.DataFrame
        Data input.
    index_by: str, default "cote_rue_id"
        Column's name to filter.

    Return
    ------
    pandas.DataFrame
        Data wihtout duplicate values in column <index_by>
    """
    return frame.groupby(index_by).nth(0).reset_index()


def upload(app_url: str, project_name: str, road_list: List[int],
           description: str = None, active_session: str = None,
           key: str = None) -> None:
    """
    Upload a capacity project onto the server.

    Parameters
    ---------
    app_url: str
        Endpoint of the server
    project_name: str
        Name of the project
    road_list: List[int]
        List of road ids
    description: str, default None
        Description of the project
    """
    payload = {
            'name': project_name,
            'description': description,
            'geobaseIds': road_list,
    }

    if key:
        payload['apiKey'] = key

    if active_session:
        log.debug('An active session is used')
        response = active_session.post(app_url, json=payload, timeout=600)
    else:
        log.debug('Api key is used')
        log.debug('Payload : %s', payload)
        log.debug('App URL : %s', app_url)
        response = requests.post(app_url, json=payload, timeout=1000)

    if response.status_code == 200:
        log.info(project_name + ': Upload successfull')
        log.info(project_name + ' ID : '+ response.json()['projectId'])
        return response.json()['projectId']

    print('There has been an error. Status : ', response.status_code)
    log.info(response.text)
    return -1


def gen_outputs(path: str, names: str, frame: pd.DataFrame,
                sector_id: str = SECTOR_NAME, road_id: str = GEOBASE_IDX_COL):
    """
    Write all ids of roads for the capacity project.

    Parameters
    ----------
    path: str
        Where to save the file
    names: str
        Name of the project
    frame: pandas.DataFrame
        Road data of the project
    sector_id: str, default NomSecteur
        Sector column's name
    road_id: str, default COTE_RUE_ID
        Road ID column's name
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
    """
    Script execution, as follow:

    1. Parse arguments
    2. Read project limit zone and road network
    3. Clip road network to limit
    4. Upload roads id to server
    """

    config = parse_args()

    # set log
    set_verbose_level(config.verbose_count)

    # read files
    zone = gpd.read_file(config.zone)
    geobase = read_mtl_open_data(GEOBASE_PATH)

    zone = assure_same_crs(geobase, zone)

    # clip roads into zone
    roads_cut = gpd.sjoin(clean_columns_names(geobase, 'geodbl'),
                          clean_columns_names(zone, 'zoneetude'),
                          predicate='within')

    roads_cut = clean_doublons(roads_cut,
                               index_by=config.geobase_id.lower())

    user = config.user
    password = config.pwd
    session = connect(url=APP_URL+API_CONNECT, user=user, password=password) if user else None
    key = config.api_key

    # Each sub-secteur have one capacity project unless specified
    # otherwise by user imput.
    if config.merge_sect:
        road_list = [int(i) for i in roads_cut[config.geobase_id.lower()].tolist()]

        if config.print_only:
            print(road_list)
        else:
            upload(
                app_url=APP_URL,
                project_name=config.project_name,
                road_list=road_list,
                description=config.project_desc,
                active_session=session,
                key=key
            )
        sys.exit(0)

    projects_id = []
    for sector, sector_roads in roads_cut.groupby(config.zone_id.lower()):
        road_list = [int(i) for i in sector_roads[config.geobase_id.lower()].tolist()]

        if config.print_only:
            print('---------' + sector + '---------')
            print(road_list)
        else:

            projects_id.append(
                upload(
                    app_url=APP_URL+API_CREATE,
                    project_name=config.project_name + " - " + str(sector),
                    road_list=road_list,
                    description=config.project_desc,
                    active_session=session,
                    key=key,
                )
            )

    #TODO: Do something with the projects ids
    log.info(projects_id)

    sys.exit(0)


if __name__ == "__main__":
    main()
