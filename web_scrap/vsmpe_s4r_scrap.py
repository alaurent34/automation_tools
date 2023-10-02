import os
import sys
import requests
import json
from typing import Tuple

URL = "https://spectrum.montreal.ca/connect/analyst/controller/connectProxy/rest/Spatial/FeatureService?url=/tables/19_VSMPE/Transport/VSMPE_TRA_SRRR_TRONCON/features.json/{}"

def save_json(data:dict, filename:str) -> None:
    filename = os.path.normpath(filename)
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'w+') as f:
        json.dump(data, f)

def iterate(index) -> Tuple[dict, int]:

    data = []
    while(True):
        print('Current data index: ' + str(index), end='\r')

        html_resp = requests.get(URL.format(index))

        # ensure of the validity of the answer
        if html_resp.status_code != 200:
            print(html_resp.text)
            sys.exit(2)

        array = json.loads(html_resp.text)
        features = array['features']

        if not features:
            print('Ended at index: '+ str(index))
            # we are at the end of the database
            break

        data += features
        index += 1

    return data, index

def main(start):

    i = start

    start_idx = i
    data, stop_idx = iterate(i)

    print(start_idx, stop_idx)
    while((start_idx + 1 < stop_idx) or start_idx < ):
        start_idx = stop_idx + 1
        data_i, stop_idx = iterate(start_idx)
        print(start_idx, stop_idx)
        save_json(data_i, f'/output/cache/data_{start_idx}_{stop_idx}')
        data += data_i

    data = {
        'type': 'FeatureCollection',
        'features': data,
        'crs': {'type': 'name', 'properties': {'name': 'epsg:42104'}}
    }

    save_json(data, './output/s3r_vsmpe.geojson')

if __name__ == '__main__':
    main(1)
