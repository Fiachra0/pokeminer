# -*- coding: utf-8 -*-
from datetime import datetime
import argparse
import json

import requests
from flask import Flask, render_template
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map
from flask_googlemaps import icons
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import config as app_config
import db
import utils

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


with open('credentials.json') as f:
    credentials = json.load(f)

with open('locales/pokemon.en.json') as f:
    pokemon_names = json.load(f)


GOOGLEMAPS_KEY = credentials.get('gmaps_key', None)
AUTO_REFRESH = 45  # refresh map every X s

#for time work
def normalize_timestamp(timestamp):
    return int(float(timestamp) / 120.0) * 120

#get arguments for the analytics python script
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-H',
        '--host',
        help='Set web server listening host',
        default='127.0.0.1'
    )
    parser.add_argument(
        '-P',
        '--port',
        type=int,
        help='Set web server listening port',
        default=5000
    )
    parser.add_argument(
        '-d', '--debug', help='Debug Mode', action='store_true'
    )
    parser.set_defaults(DEBUG=True)
    return parser.parse_args()

def create_app():
    app = Flask(__name__, template_folder='templates')
    GoogleMaps(app, key=GOOGLEMAPS_KEY)
    return app

app= create_app()

#for an analytics dashboard in the future
@app.route('/')
def dashboard():
    return render_template(
		'newmap.html'
    )


#Create REST API for map config
@app.route('/config')
def config():
    """Gets the settings for the Google Maps via REST"""
    map_center = utils.get_map_center()
    return json.dumps({
        'lat': map_center[0],
        'lng': map_center[1],
        'zoom': 15,
        'identifier': 'fullmap'
    })

@app.route('/data')
def pokemon_data():
    return json.dumps(get_pokemarkers())

#Route for  API calls formatted into JSON
@app.route('/pokemon/<pokemon_id>/json')
def pokemon_json(pokemon_id):
  pokemon_id2 = "1"
  for pokedex_number, pokemon_name in pokemon_names.items():
	if  pokedex_number == str(pokemon_id) or pokemon_name.lower() == str(pokemon_id).lower():
                return json.dumps(search_pokemon(pokedex_number))
  return "not a pokemon"

#route for finding top seen pokemon
@app.route('/pokemon/top/json')
def find_most_seen():
  return json.dumps(search_top_pokemon('10','DESC'))

#route for finding least seen pokemon
@app.route('/pokemon/bottom/json')
def find_least_seen():
  return json.dumps(search_top_pokemon('10','ASC'))

#route for finding all seen pokemon
@app.route('/pokemon/all/json')
def find_all_seen():
  return json.dumps(search_top_pokemon('151','DESC','pokemon_id'))

#route for finding most common spawns
@app.route('/pokemon/spawns/all/json')
def find_common_spawns():
  return json.dumps(search_common_spawns('100','DESC'))

#route for finding a pokemons common spawns
@app.route('/pokemon/spawns/<pokemon_id>/json')
def find_common_pokemon_spawns(pokemon_id):
  for pokedex_number, pokemon_name in pokemon_names.items():
	if  pokedex_number == str(pokemon_id) or pokemon_name.lower() == str(pokemon_id).lower():
	   return json.dumps(search_common_pokemon_spawns(pokemon_id))
  return "not a pokemon"

#route for finding what spawned at this point
@app.route('/pokemon/spawns/<lat>/<lon>/json')
def find_spawned_at(lat,lon):
  return json.dumps(search_pokemon_spawned_at(lat,lon))


#route for pokemon maps
@app.route('/pokemon/<pokemon_id>')
def fullmap(pokemon_id):
    for pokedex_number, pokemon_name in pokemon_names.items():
        if  pokedex_number == str(pokemon_id) or pokemon_name.lower() == str(pokemon_id).lower():
    	    return render_template(
        	'historical-map.html',
       		 key=GOOGLEMAPS_KEY,
       		 fullmap=get_map(),
		 auto_refresh=AUTO_REFRESH * 1000
       	    )
    return "not a pokemon"

#queries the database and sends the result back
def search_top_pokemon(count, order, order_by='how_many'):
  session = db.Session()
  pokemons = db.get_top_pokemon(session,count,order, order_by)
  session.close
  for pokemon in pokemons:
	for pokedex_number,pokedex_name in pokemon_names.items():
	  if str(pokemon['pokemon_id']) == pokedex_number:
		pokemon.update({'name': pokedex_name})
  return pokemons

#queries the database and sends the result back
def search_common_spawns(count, order):
  session = db.Session()
  pokemons = db.get_common_spawns(session,count,order)
  session.close
  return pokemons

#queries the database to find which pokemon spawned at the coords
def search_pokemon_spawned_at(lat,lon):
  session = db.Session()
  pokemons = db.get_pokemon_spawned_at(session,lat,lon)
  session.close
  return pokemons

#queries the database to find which  spawns are common for this pokemon
def search_common_pokemon_spawns(pokemon_id, order='DESC', count=100):
  session = db.Session()
  pokemons = db.get_common_pokemon_spawns(session,pokemon_id,order,count)
  session.close
  return pokemons


#open a session and query for pokemon seen by pokedex_entry
def search_db(pokedex_number):
  session = db.Session()
  pokemons = db.get_pokemon_history(session,pokedex_number)
  session.close
  return pokemons

#queries the database session then formats to be returned in an array
def search_pokemon(pokedex_number):
  print "[!] Searching For: " + pokedex_number.title()
  pokemons = search_db(pokedex_number)
  found_pokemons = []
  for pokemon in pokemons:
        name = pokemon_names[str(pokemon.pokemon_id)]
        datestr = datetime.fromtimestamp(pokemon.expire_timestamp)
        dateoutput = datestr.strftime("%H:%M:%S")

        LABEL_TMPL = u'''
<div><b>{name}</b><span> - </span><small><a href='http://www.pokemon.com/us/pokedex/{id}' target='_blank' title='View in Pokedex'>#{id}</a></small></div>
<div>Disappears at - {disappear_time_formatted} <span class='label-countdown' disappears-at='{disappear_time}'></span></div>
<div><a href='https://www.google.com/maps/dir/Current+Location/{lat},{lng}' target='_blank' title='View in Maps'>Get Directions</a></div>
'''
        label = LABEL_TMPL.format(
            id=pokemon.pokemon_id,
            name=name,
            disappear_time=pokemon.expire_timestamp,
            disappear_time_formatted=dateoutput,
            lat=pokemon.lat,
            lng=pokemon.lon,
        )
        #  NOTE: `infobox` field doesn't render multiple line string in frontend
        label = label.replace('\n', '')


	found_pokemons.append({
 	    'type': 'pokemon',
            'name': name,
            'key': '{}-{}'.format(pokemon.pokemon_id, pokemon.spawn_id),
            'expire_time':pokemon.expire_timestamp,
	    'normalized_expire_time': (datetime.fromtimestamp(pokemon.expire_timestamp)).strftime("%H:%M:%S"),
            #'icon': 'static/icons/%d.png' % pokemon.pokemon_id,
            'lat': pokemon.lat,
            'lng': pokemon.lon,
            'pokemon_id': pokemon.pokemon_id,
	    'infobox':label
	})
  return  found_pokemons


def get_map():
    map_center = utils.get_map_center()
    fullmap = Map(
        identifier='fullmap2',
        style='height:100%;width:100%;top:0;left:0;position:absolute;z-index:200;',
        lat=map_center[0],
        lng=map_center[1],
        markers=[],  # will be fetched by browser
        zoom='15',
    )
    return fullmap


if __name__ == '__main__':
    args = get_args()
    app.run(debug=True)
