import os
import requests
import json

# Change cookies
cookies = {
            'JSESSIONID': 'A6754878CA5A71B500331A595C8CD281',
            '_ga': 'GA1.2.1015398938.1638906416',
            '_ga_MNCT7KCK9D': 'GS1.1.1655489002.4.0.1655489004.0',
            'portal_recent_boroughs': '[%22VSMPE%22%2C%22%22%2C%22%22]',
            'portal_selected_borough': 'VSMPE',
}

headers = {
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

# Querry the whole database from "19_VSMPE/Transport/VSMPE_TRA_SRRR_TRONCON"
data = "url=tables%2Ffeatures.json&encodeSpecialChars=true&postData=%7B%22query%22%3A%22SELECT%20*%20From%20%5C%22%2F19_VSMPE%2FTransport%2FVSMPE_TRA_SRRR_TRONCON%5C%22%20%20%22%7D"

def save_json(data:dict, filename:str) -> None:
    filename = os.path.normpath(filename)
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'w+') as f:
        json.dump(data, f)


response = requests.post(
    'https://spectrum.montreal.ca/connect/analyst/controller/connectProxy/rest/Spatial/FeatureService',
    cookies=cookies,
    headers=headers,
    data=data,
)

data = json.loads(response.text)

save_json(data, 'output/vsmpe_srrr_troncon.geojson')
