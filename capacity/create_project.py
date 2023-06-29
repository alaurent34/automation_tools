# -*- coding: utf-8 -*-
"""
Created on Thu Oct 13 10:31:02 2022

@author: lgauthier
"""

import geopandas as gpd
import datetime
import os

GEOBASE_IDX_COL = 'COT_RUE_ID'
SECTOR_NAME = 'NomSecteur'

PROJECT_PATH = r"C:/Users/alaurent/OneDrive - Agence de mobilité durable/Shared Documents/23513_SDÉ_Accessibilité artères commerciales/03_Travail/31_Analyses/Préparation"
NOM_FICHIER_ZONE_ETUDE = r"23513_zones d'études.geojson"

GEODOUBLE = gpd.read_file(r"C:/Users/alaurent/OneDrive - Agence de mobilité durable/Shared Documents/General/Données communes/Geobases/2023-05/geobase double")
ZONEETUDE = gpd.read_file(os.path.join(PROJECT_PATH, NOM_FICHIER_ZONE_ETUDE))

date = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

def clean_columns_names(df, suffix):
    names = {x:x.lower()+f'_{suffix.lower()}' if x.lower() == 'id' else x.lower() for x in df.columns}
    return df.rename(columns=names)

def clean_doublons(frame, field=GEOBASE_IDX_COL.lower()):
    return frame.groupby(field).nth(0).reset_index()

def genOutputs(path, names, frame):
    frame.to_file(os.path.join(path, names+".geojson"), index=False, driver='GeoJSON')

    for sector, data in frame.groupby(SECTOR_NAME.lower()):
        with open(os.path.join(PROJECT_PATH, path, names + sector + "_asList.txt"), 'w') as f:
            f.write(",\n".join([str(i) for i in data[GEOBASE_IDX_COL.lower()].tolist()]))


roadsCut = gpd.sjoin(clean_columns_names(GEODOUBLE, 'geodbl'),
                     clean_columns_names(ZONEETUDE, 'zoneetude'),
                     predicate='within')
roadsCut = clean_doublons(roadsCut)

genOutputs(PROJECT_PATH, f"geoDoubleExtract_{date}", roadsCut)