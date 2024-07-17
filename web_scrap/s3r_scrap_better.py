import os
import copy
import json
import requests

###################################
####### CHANGE THOSE VARS #########
###################################

ARRND_TABLE_SRRR_SECT = {
    'Lachine': '/04_Lachine/SRRR/LAC_SRRRsecteur',
    'Plateau Mont-Royal': '/06_PMR/CirEtStat/PMR_CircStat_SRRR_Sect',
    'Le Sud-Ouest': '/07_SO/Stat/SO_Stat_SRRR_secteurs',
    'Verdun': '/17_Verdun/StatSRRR/VER_Stat_SRRR_secteurs',
    'Ville-Marie': '/18_VM/SecStatRes/VM_Secteur_stationnement_resid',
    'Villeray-Saint-Michel-Parc-Extension': '/19_VSMPE/Transport/VSMPE_TRA_SRRR_1'
}

ARRND_TABLE_SRRR_ZONE = {
    'Lachine': '/04_Lachine/SRRR/LAC_SRRRzone',
    'Plateau Mont-Royal': '/06_PMR/CirEtStat/PMR_CircStat_SRRR_Zone',
    'Le Sud-Ouest': '/07_SO/Stat/SO_Stat_SRRR',
    'Verdun': '/17_Verdun/StatSRRR/VER_Stat_SRRR_1',
    'Villeray-Saint-Michel-Parc-Extension': '/19_VSMPE/Transport/VSMPE_TRA_SRRR_TRONCON'
}

DATA_TO_FETCH = {
    'SRRR_Secteur': ARRND_TABLE_SRRR_SECT,
    'SRRR_Zone': ARRND_TABLE_SRRR_ZONE
}

#################################
####### CHANGE END HERE #########
#################################

HEADERS = {
    'authority': 'spectrum.montreal.ca',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://spectrum.montreal.ca',
    'referer': 'https://spectrum.montreal.ca/connect/analyst/mobile/',
    'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
}

URL = 'https://spectrum.montreal.ca/connect/analyst/controller/connectProxy/rest/Spatial/FeatureService'

QUERY = {
        "query":"SELECT * From \"{}\" "
}

PARAMS = {
        'url': 'tables/features.json',
        'encodeSpecialChars': True,
        'postData': None
}

def save_json(data:dict, filename:str) -> None:
    filename = os.path.normpath(filename)
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'w+') as f:
        json.dump(data, f)

def build_query(table: str):
    query = copy.deepcopy(QUERY)
    query['query'] = query['query'].format(table)

    return query

def build_params(table: str):
    query = build_query(table)
    params = copy.deepcopy(PARAMS)

    params['postData'] = json.dumps(query)

    return params

def add_limits_params(params, limits, last_id=0):
    params = copy.deepcopy(params)
    params['postData'] = params['postData'].replace(
            '"}',
            ' ORDER BY ID LIMIT ' + str(limits) + ' OFFSET ' + str(last_id) + '"}'

    )

    return params

def query(session: requests.Session, url: str, params: dict):
    req = session.post(url, params=params)

    if 'message' in req.json() and req.json()['message'] == "Maximum number of features (1000) reached.":
        i = 0
        res = {}
        while True:
            paramsl = add_limits_params(params, 999, i)
            req = session.post(url, params=paramsl)
            i+= 999
            if req.json()['features']:
                if not res:
                    res = req.json()
                else:
                    res['features'].append(req.json()['features'])
            else:
                return res

    return req.json()

def main():

    s = requests.Session()
    s.headers = HEADERS

    os.makedirs('output', exist_ok=True)
    for type_geom, arnd_conf in DATA_TO_FETCH.items():
        print(f'Querying {type_geom}')
        os.makedirs(f'output/{type_geom}/', exist_ok=True)
        for arnd, query_table in arnd_conf.items():
            print(f'Querying {type_geom} for district', arnd, end="\r")
            params = build_params(query_table)
            data = query(s, URL, params)
            data['crs'] = {
                            "type": "name",
                            "properties": {
                                "name": "epsg:2950"
                            }
                        }
            save_json(data, f'output/{type_geom}/{arnd}.geojson')



if __name__ == '__main__':
    main()

# req = requests.Request('POST', URL, params=PARAMS)
# prepped = s.prepare_request(req)
# print(prepped.url)
# response = requests.post(
#     url=URL,
#     cookies=cookies,
#     headers=headers,
#     params=PARAMS
# )

# print(response.json)

# data = json.loads(response.text)

# save_json(data, 'output/vsmpe_srrr_troncon.geojson')
