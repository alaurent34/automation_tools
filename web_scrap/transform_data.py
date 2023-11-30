import itertools
from operator import itemgetter
from typing import List

import numpy as np
import pandas as pd
import geopandas as gpd
from centerline.geometry import Centerline
from shapely import geometry, ops, GeometryType

from geom import multipointobject_left_or_right

DEFAULT_REG = {
    'deb': 0.0,
    'fin': 0.0,
    'res_date_debut ': np.nan,
    'res_date_fin': np.nan,
    'res_days': np.nan,
    'res_hour_from': np.nan,
    'res_hour_to': np.nan,
    'res_type': 'SRRR',
    'restrictions': 'Aucune places',
    'longueur_non_marquée': 0.0,
    'nb_places_total': 0
}

def approximate_medial_axis(polygon):
    """ This is an approximation for buffered linestrign like polygon.
    It only keep the longuest segment of the polygon skeleton.

    Parameters
    ----------
    polygon: shapely.geometry.Polygon
        Polygon on which to compute the medial axis.

    Returns
    -------
    line: shapely.geometry.LineString
    """

    skeleton = Centerline(polygon).geometry

    skeleton = ops.linemerge(skeleton)

    skeleton_part_size = [x.length for x in skeleton.geoms]

    return skeleton.geoms[np.argmax(skeleton_part_size)]

def approximate_medial_axis_rect(rectangle):
    """ This is an approximation for a rectangle.
    It retrun the medial axis of the rotated rectangle
    envelope of this prolygon.

    Parameters
    ----------
    rectangle: shapely.geometry.Polygon
        Polygon on which to compute the medial axis.

    Returns
    -------
    line: shapely.geometry.LineString
    """
    if isinstance(rectangle, MultiPolygon):
        if len(list(rectangle.geoms))>1:
            raise(NotImplementedError, "Multipolygones are not implementend.")
        rectangle = rectangle.geoms[0]

    medial_axis_candidates = list(rectangle.minimum_rotated_rectangle.exterior.coords)


    return LineString([medial_axis[0], medial_axis[3]])

def parse_regulation_string(df:pd.Series):
    """ Take a regulation serie string at s3r format and parse information about
    hour start, hour end, days and active period.
    """

    hour_and_days_reg = df.str.extractall(
            r"^(?P<res_hour_from>\d+h\d+) à "+
            "(?P<res_hour_to>\d+h\d+) du "+
            "(?P<res_day_from>\w{3}).+ au (?P<res_day_to>\w{3}).+$"
    )
    hour_only_reg = df.str.extractall(
            r"^(?P<res_hour_from>\d+h\d+) à "+
            "(?P<res_hour_to>\d+h\d+)$"
    )

    # assert that index are not overlapping
    assert np.intersect1d(
        hour_and_days_reg.reset_index(level=1).index,
        hour_only_reg.reset_index(level=1).index
    ).shape[0] == 0

    # format days span
    hour_and_days_reg['res_days'] = hour_and_days_reg['res_day_from'] + '-' + \
                                    hour_and_days_reg['res_day_to']

    # concat both dataset
    regs = pd.concat([hour_and_days_reg, hour_only_reg]).reset_index(level=1,
                                                                     drop=True)

    return regs

def linear_referencing_linestring(line1: geometry.LineString, line2: geometry.LineString):
    """ Perform the linear referencing of one line on the other.

    Parameters
    ----------
    line1: shapely.LineString
    line2: shapely.LineString

    Returns
    -------
    shapely.Point
        First point postion on line2
    shapely.Point
        Second point postion on line2
    """
    pt1 = geometry.Point(line1.coords[0])
    pt2 = geometry.Point(line1.coords[-1])

    pt1_proj = line2.project(pt1)
    pt2_proj = line2.project(pt2)

    if pt1_proj > pt2_proj:
        return pt2_proj, pt1_proj

    return pt1_proj, pt2_proj

def compute_linear_ref_on_roads(df:gpd.GeoDataFrame,
                                roads:gpd.GeoDataFrame, join_on='ID_TRC'):
    df = df.copy()
    roads = roads.copy()

    roads = roads.rename_geometry('road_geom')

    df = df.join(roads.set_index(join_on)[['road_geom']], on=join_on)

    df['deb'], df['fin'] = zip(*df.apply(
        lambda x: linear_referencing_linestring(x.geometry, x.road_geom),
        axis=1
    ))

    df = df.drop(columns='road_geom')

    return df


def compute_left_or_right_linestring(df:gpd.GeoDataFrame,
                                     roads:gpd.GeoDataFrame, join_on='ID_TRC'):
    """ Compute on which side of the road each element of s3r_df lands.

    Parameters
    ----------
    df: geopandas.GeoDataFrame

    roads: geopandas.GeoDataFrame

    Return
    ------
    gpd.GeoDataFrame
        df enhanced with side_of_street column.
    """

    df_crs = df.crs

    df = df.copy()
    roads = roads.copy()

    df = df.to_crs('epsg:4326')
    roads = roads.to_crs('epsg:4326')
    roads = roads.rename_geometry('road_geom')

    df = df.join(roads.set_index(join_on)[['road_geom']], on=join_on)

    df['side_of_street'] = df.apply(
            lambda x: multipointobject_left_or_right(x.road_geom,
                                                     geometry.Point(x.geometry.coords[0])),
            axis=1)

    df = df.to_crs(df_crs)
    df = df.drop(columns='road_geom')

    return df

def find_nearest_road(df:gpd.GeoDataFrame, roads:gpd.GeoDataFrame, **kwargs):
    """ For each geometry in df, find the closest road associated with it.
    """

    return gpd.sjoin_nearest(df, roads, **kwargs)


def finalize(df:gpd.GeoDataFrame):
    df = df.rename(columns={
        'ID_TRC':'segment',
        'LONGUEUR_STAT': 'longueur_non_marquée',
        'NBRE_CASE_STAT': 'nb_places_total',
    })

    for col, default in DEFAULT_REG.items():
        if col in df.columns:
            continue
        df[col] = default

    # remove restriction that are 0 meter
    df = df[df.deb + 5 < df.fin]

    return df[['segment'] + list(DEFAULT_REG.keys()) + ['side_of_street']]

def main():

    # read data
    print('Read data')
    df = gpd.read_file('output/vsmpe_srrr_troncon_POLYGON.geojson')
    roads = gpd.read_file('../capacity/assets/geobase_simple.geojson')
    delim = gpd.read_file('../../lapin/data/limites/23505_Parc_Jarry.geojson')

    # transform crs to Montreal
    df = df.to_crs('epsg:32188')
    roads = roads.to_crs('epsg:32188')
    delim = delim.to_crs('epsg:32188')

    # get the medial axis
    print('Medial axis computation')
    df.geometry = df.geometry.apply(approximate_medial_axis)

    # process SRRR reglementation
    print('SRRR regulation parsing')
    df = df.join(parse_regulation_string(df.HEURE), how='left')

    # find clothest roads
    print('Clothest roads join')
    df = find_nearest_road(
            df,
            roads[['ID_TRC', 'geometry']],
            how='left',
            exclusive=True,
            max_distance=10,
    )
    # if two or more roads are at equal distance of a segment,
    # only keep the first one.
    # df = df.groupby(level=0).nth(0)

    # compute side_of_street
    print('Side of street computation')
    df = compute_left_or_right_linestring(df, roads, join_on='ID_TRC')

    # compute linear referencing
    print('Linear referencing computation')
    df = compute_linear_ref_on_roads(df, roads, join_on='ID_TRC')

    # cut roads that are outside delim
    df = gpd.sjoin(
            left_df=df.drop(columns=['index_right', 'index_left'], errors='ignore'),
            right_df=delim,
            how='inner',
            predicate='within'
    )

    # make it into regulation
    print('Final touch')
    df = finalize(df)

    # save
    print('Save')
    df.drop(columns='res_date_debut ').to_csv('./output/srrr_regulation_vsmpe.csv', index=False)

if __name__ == '__main__':
    main()
