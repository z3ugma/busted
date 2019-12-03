from flask import Flask, jsonify
import requests, os, json

app = Flask(__name__)

GEOCODIO_API_KEY = os.environ.get("GEOCODIO_API_KEY")
route = 95

@app.route('/')
def hello_world():

    response = {'vehicles': [], 'stops': []}

    url = "http://webwatch.cityofmadison.com/TMWebWatch/GoogleMap.aspx/getVehicles"
    payload = json.dumps({'routeID': route})
    headers = {
        'Content-Type': "application/json",
        'cache-control': "no-cache",
        }
    response['vehicles'] = json.loads(requests.request("POST", url, data=payload, headers=headers).text)['d'] or []

    url = "http://webwatch.cityofmadison.com/TMWebWatch/GoogleMap.aspx/getStopTimes"
    payload = json.dumps({"stops":[{"routeID":route,"directionID":14,"stopID":964,"timePointID":304},{"routeID":route,"directionID":211,"stopID":964,"timePointID":304}]})
    response['stops'] = list(filter(lambda x: x['routeID'] == route, json.loads(requests.request("POST", url, data=payload, headers=headers).text)['d']['routeStops']))[0]['stops'] or []


    address_sets = json.dumps([ "{}, {}".format(a['lat'], a['lon']) for a in response['vehicles']])
    if address_sets != "[]" and response['vehicles'] != []:
        url = "https://api.geocod.io/v1.4/reverse"
        querystring = {"api_key": GEOCODIO_API_KEY}
        coded_addresses = requests.request("POST", url, data=address_sets, headers=headers, params=querystring)

        for idx,v in enumerate(coded_addresses.json().get('results')) or []:
            nearest_streets = " / ".join(list(set([ ' '.join([ (i['address_components'].get('predirectional') or ''), i['address_components']['street'] ]).strip() for i in v['response']['results']])))
            response['vehicles'][idx]['address'] = nearest_streets
    
    return jsonify(response)