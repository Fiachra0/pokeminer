import json
from pushbullet import Pushbullet
from geopy.geocoders import Nominatim
from datetime import datetime
import sys
import config

import requests
from spark.rooms import Room
from spark.session import Session

with open('locales/pokemon.en.json') as f:
    pokemon_names = json.load(f)

# Fixes the encoding of the male/female symbol
reload(sys)  
sys.setdefaultencoding('utf8')

pushbullet_client = None
wanted_pokemon = None

# Initialize object
def init():
    global room,spark_room,spark_client, wanted_pokemon

    # get list of pokemon to send notifications for
    wanted_pokemon = _str( config.WANTED_POKEMON ) . split(" ,")
    # transform to lowercase
    wanted_pokemon = [a.lower() for a in wanted_pokemon]

    # get api key
    api_key = _str( config.SPARK_KEY )
    
    if api_key:
          spark_client = Session('https://api.ciscospark.com', api_key)
	  spark_room = config.SPARK_ROOM
	  # pushbullet_client = Pushbullet(api_key)
	  # channel = pushbullet_client.channels[0]
    try:
        spark_room = Room.get(spark_client, spark_room)
    except ValueError:
        exit("  Exiting as I failed to authenticate your Spark API key")
    
# Safely parse incoming strings to unicode
def _str(s):
  return s.encode('utf-8').strip()

# Notify user for discovered Pokemon
def pokemon_found(pokemon):
    # get name
    pokename = str(pokemon_names[str(pokemon.pokemon_id)]).lower()
    # check array
    if not spark_client or not pokename in wanted_pokemon: return
    # notify
    print "[+] Notifier found pokemon:", pokename
    #address =unicode( Nominatim().reverse(str(pokemon["lat"])+", "+str(pokemon["lng"])).address)
    #http://maps.google.com/maps/place/<place_lat>,<place_long>/@<map_center_lat>,<map_center_long>,<zoom_level>z
 
    #variables for pushing
    latLon = '{},{}'.format(repr(pokemon.lat), repr(pokemon.lon))
    google_maps_link_tmpl = '<a href=\"http://maps.google.com/maps?q={latLon}\">Locate on Google Maps </a>'
    google_maps_link = google_maps_link_tmpl.format(
    latLon=latLon
    ) 
    notification_text = "<b>Pokemon Finder found " + pokename.title() + "!</b>"
    disappear_time = str(datetime.fromtimestamp(pokemon.expire_timestamp).strftime("%I:%M%p").lstrip('0'))
    location_text =  google_maps_link
    disappear_text =str(pokename).title()  + " will be available until " + disappear_time + "."

    #create message template
    message_tmpl =u'''
{notification_text}

{disappear_text}
{location_text}
    '''

    #Insert the variables into the template
    message = message_tmpl.format(
    notification_text=notification_text,
    location_text=location_text,
    disappear_text=disappear_text
    )

    #push = channel.push_note(notification_text,location_text)
    spark_room.send_message(spark_client,message,'html')

def test():
    spark_room.send_message(spark_client,'test','html')
     

init()


