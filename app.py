from flask import Flask, jsonify, render_template
import requests, os, json, datetime
import pyjade
from flask_assets import Environment, Bundle

app = Flask(__name__)
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

from webassets.filter import get_filter

libsass_source = get_filter(
    'libsass',
    style='compressed'
)

assets = Environment(app)
assets.url = app.static_url_path
# assets.debug = True
sass = Bundle('sass/app.sass', filters=libsass_source, depends=('sass/**/*.sass', 'sass/*.sass'), output='css/app.css')
assets.register('sass_all', sass)

GEOCODIO_API_KEY = os.environ.get("GEOCODIO_API_KEY")
route = 95 #66 is 11 bus, 95 is 12 bus
stops = {964: "Main & Carroll", 3586: "John Nolen at Lakeside NB"}

def get_info():

    response = {'vehicles': [], 'stops': [], 'timestamp': datetime.datetime.now().strftime('%-I:%M:%S %p %a')}

    url = "http://webwatch.cityofmadison.com/TMWebWatch/GoogleMap.aspx/getVehicles"
    payload = json.dumps({'routeID': route})
    headers = {
        'Content-Type': "application/json",
        'cache-control': "no-cache",
        }
    response['vehicles'] = json.loads(requests.request("POST", url, data=payload, headers=headers).text)['d'] or []
    
    url = "http://webwatch.cityofmadison.com/TMWebWatch/GoogleMap.aspx/getStopTimes"
    payload = json.dumps(
        {"stops":[
            {"routeID": route, "directionID": 14, "stopID": 964}, # Toward Dutch Mill 964 Main @ Carrol (1101)
            {"routeID": route, "directionID": 211, "stopID": 3586} # Toward WTP 3586 JN at Lakeside NB (0621)
            ]
        }
    )

    response['stops'] = json.loads(requests.request("POST", url, data=payload, headers=headers).text)['d']['routeStops'][0]['stops'] or []
    for s in response['stops']:
        s['name'] = stops.get(s['stopID'], s['stopID'])
    response['stops'] = list(filter(lambda x: x['crossings'] is not None, response['stops']))
    address_sets = json.dumps([ "{}, {}".format(a['lat'], a['lon']) for a in response['vehicles']])
    if address_sets != "[]" and response['vehicles'] != []:
        url = "https://api.geocod.io/v1.4/reverse"
        querystring = {"api_key": GEOCODIO_API_KEY}
        coded_addresses = requests.request("POST", url, data=address_sets, headers=headers, params=querystring)

        for idx,v in enumerate(coded_addresses.json().get('results')) or []:
            nearest_streets = " / ".join(list(set([ ' '.join([ (i['address_components'].get('predirectional') or ''), i['address_components']['street'] ]).strip() for i in v['response']['results']])))
            response['vehicles'][idx]['address'] = nearest_streets
    
    return response

@app.template_filter('adherence_color')
def adherence_color(c):
    if c == None:
        return "is-dark"
    elif int(c) >=0:
        return "is-primary"
    elif int(c) <-5:
        return "is-danger"    
    elif int(c) <0:
        return "is-warning"
    else:
        return "is-dark"

@app.template_filter('adherence_display')
def adherence_display(c):
    if c is None:
        return "?"
    else:
        return abs(c)

@app.route('/')
def index():
    info = get_info()
    return render_template("index.jade", info=info)

@app.route('/api')
def index_json():
    return jsonify(get_info())
