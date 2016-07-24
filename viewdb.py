import db
import json
from datetime import datetime

session = db.Session()
pokemons = db.get_sightings(session)
session.close()

with open('locales/pokemon.en.json') as f:
    pokemon_names = json.load(f)

for pokemon in pokemons:
        name = pokemon_names[str(pokemon.pokemon_id)]
        datestr = datetime.fromtimestamp(pokemon.expire_timestamp)
        dateoutput = datestr.strftime("%H:%M:%S")
	pokemonEntry = name +" "+str( datestr) +" "+ str(dateoutput)
	print pokemonEntry

