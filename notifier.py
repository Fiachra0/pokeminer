import json
from pushbullet import Pushbullet
from datetime import datetime
import sys
import config

with open('locales/pokemon.en.json') as f:
    pokemon_names = json.load(f)

# Fixes the encoding of the male/female symbol
reload(sys)  
sys.setdefaultencoding('utf8')

pushbullet_client = None
wanted_pokemon = None

# Initialize object
def init():
    global channel,pushbullet_client, wanted_pokemon

    # get list of pokemon to send notifications for
    wanted_pokemon = _str( config.WANTED_POKEMON ) . split(" ,")
    # transform to lowercase
    wanted_pokemon = [a.lower() for a in wanted_pokemon]

    # get api key
    api_key = _str( config.PUSHBULLET_KEY )
    if api_key:
           pushbullet_client = Pushbullet(api_key)
	   channel = pushbullet_client.channels[0]


# Safely parse incoming strings to unicode
def _str(s):
  return s.encode('utf-8').strip()

# Notify user for discovered Pokemon
def pokemon_found(pokemon):
    # get name
    pokename = str(pokemon_names[str(pokemon.pokemon_id)]).lower()
    # check array
    if not pushbullet_client or not pokename in wanted_pokemon: return
    # notify
    print "[+] Notifier found pokemon:", pokename
    address = Nominatim().reverse(str(pokemon["lat"])+", "+str(pokemon["lng"])).address
    #http://maps.google.com/maps/place/<place_lat>,<place_long>/@<map_center_lat>,<map_center_long>,<zoom_level>z
    latLon = '{},{}'.format(repr(pokemon.lat), repr(pokemon.lon))
    google_maps_link = 'http://maps.google.com/maps?q=' + str(pokemon.lat) +"," + str(pokemon.lon)

    notification_text = "Pokemon Finder found " + pokename + "!"
    disappear_time = str(datetime.fromtimestamp(pokemon.expire_timestamp).strftime("%I:%M%p").lstrip('0'))+")"
    location_text = "Go search at this location: " + address + ". Locate on Google Maps : " + google_maps_link + ". " + str(pokename) + " will be available until " + disappear_time + "."

    push = channel.push_note(notification_text,location_text)



init()