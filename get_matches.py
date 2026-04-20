from dotenv import load_dotenv
import os
import requests
import time
import tqdm
import json

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": API_KEY}

PLATFORM = "https://euw1.api.riotgames.com"
REGIONAL = "https://europe.api.riotgames.com"


def _get(url, params=None, retries=3):
    for attempt in range(retries):
        r = requests.get(url, headers=HEADERS, params=params)

        if r.status_code == 200:
            return r.json()

        elif r.status_code == 400:
            print("Error 400 : Bad Request")
            return None
        
        elif r.status_code == 401:
            print("Error 401 : Unauthorized")
            return None
        
        elif r.status_code == 403:
            print("Error 403 : Forbidden")
            return None
        
        elif r.status_code == 404:
            print("Error 404 : Not Found")
            return None
        
        elif r.status_code == 429:
            retry_after = int(r.headers.get("Retry-After", 5))
            print("Error 429 : Rate Limit Exceeded. Try again in {} seconds".format(retry_after))
            time.sleep(retry_after)
        
        elif r.status_code == 500:
            print("Error 500 : Internal Server Error")
            return None
        
        elif r.status_code == 503:
            print("Error 503 : Service Unavailable")
            return None
        else:
            print("Unknown Error {}".format(r.status_code))
            return None
    
def get_puuid_challengers_queue(queue):
    url = f"{PLATFORM}/lol/league/v4/challengerleagues/by-queue/{queue}"
    data = _get(url)
    entries = [entry['puuid'] for entry in data['entries']]
    return entries

def get_solorankedgames_from_puuid(puuid, start_time, end_time, start=0, count=100):
    entries = []
    url = f"{REGIONAL}/lol/match/v5/matches/by-puuid/{puuid}/ids"
    # make sure we have int for RiotAPI
    start_time = int(start_time)
    end_time = int(end_time)
    data = _get(url, params={'startTime':start_time, "endTime":end_time, "start": start, "count":count, "queue":420})
    entries.extend(data)
    while len(data) == 100:
        start += count
        data = _get(url, params={'startTime':start_time, "endTime":end_time, "start": start, "count":count, "queue":420})
        entries.extend(data)
    return entries

def save_metadata(metadata, name, path='./data/'):
    with open(os.path.join(path, name), "w") as f:
        json.dump(metadata, f, indent=2)

def load_metadata(path):
    with open(path, 'r') as f:
        return json.load(f)    

def get_all_challengers_gameID_from_queue(queues, start_time, end_time=time.time()):
    players_puuid = []

    # ONE API CALL PER QUEUE
    for queue in queues:
        players_puuid.extend(get_puuid_challengers_queue(queue))

    games = []
    # ONE API CALL PER 100 GAMES PER PLAYER
    for player in tqdm.tqdm(players_puuid):
        games.extend(get_solorankedgames_from_puuid(player, start_time, end_time))

    games = list(set(games))
    to_save = {'start_time': start_time,
               'end_time': end_time, 
               'games': games}
    return to_save

def initial_database(queues):
    """Initial creation of the database
    We start 6 months before the day it is created in order to get a sufficient amount of data"""
    
    start_time = time.time() - 6*30*24*60*60
    to_save = get_all_challengers_gameID_from_queue(queues, start_time)
    save_metadata(to_save, 'gamesID.json')

def refresh_database(queues, name='gamesID.json', path='./data/'):
    """Allows to refresh the database with games from the last games in the file up until the time it is launched"""
    current_games = load_metadata(os.path.join(path, name))
    new_games = get_all_challengers_gameID_from_queue(queues, current_games['end_time'])
    to_save = {'start_time' : current_games['start_time'],
               'end_time' : new_games['end_time'],
               'games': list(set(new_games['games'] + current_games['games']))}
    save_metadata(to_save, name, path)

def add_database(queues, start_time, end_time, name='gamesID.json', path='./data/'):
    """Allows to add any time period to the file where gameIDs are saved. I don't expect this function to be used much 
    but it exists if needed"""
    current_games = load_metadata(os.path.join(path, name))
    new_games = get_all_challengers_gameID_from_queue(queues, start_time, end_time)
    to_save = {'start_time' : min(new_games['start_time'], current_games['start_time']),
               'end_time' : max(new_games['end_time'], current_games['end_time']),
               'games': list(set(new_games['games'] + current_games['games']))}
    save_metadata(to_save, name, path)


queues = ["RANKED_SOLO_5x5"]