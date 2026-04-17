from dotenv import load_dotenv
import os
import requests
import time
import tqdm

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

        if r.status_code == 400:
            print("Error 400 : Bad Request")
            return None
        
        if r.status_code == 401:
            print("Error 401 : Unauthorized")
            return None
        
        if r.status_code == 403:
            print("Error 403 : Forbidden")
            return None
        
        if r.status_code == 404:
            print("Error 404 : Not Found")
            return None
        
        if r.status_code == 429:
            retry_after = int(r.headers.get("Retry-After", 5))
            print("Error 429 : Rate Limit Exceeded. Try again in {} seconds".format(retry_after))
            time.sleep(retry_after)
        
        if r.status_code == 500:
            print("Error 500 : Internal Server Error")
            return None
        
        if r.status_code == 503:
            print("Error 503 : Service Unavailable")
            return None
        else:
            print("Unknown Error {}".format(r.status_code))
            return None
    
def get_puuid_challengers_queue(queue):
    url = f"{PLATFORM}/lol/league/v4/challengerleagues/by-queue/{queue}"
    data = _get(url)
    entries = [data['entries'][i]['puuid'] for i in range(len(data['entries']))]
    return entries

def get_solorankedgames_from_puuid(puuid, startTime, start=0, count=100):
    entries = []
    url = f"{REGIONAL}/lol/match/v5/matches/by-puuid/{puuid}/ids"
    data = _get(url, params={'startTime':startTime, "start": start, "count":count, "queue":420})
    entries.extend(data)
    while len(data) == 100:
        start += count
        data = _get(url, params={'startTime':startTime, "start": start, "count":count, "queue":420})
        entries.extend(data)
    return entries

queues = ["RANKED_SOLO_5x5"]
players_puuid = []

# ONE API CALL PER QUEUE
for queue in queues:
    players_puuid.extend(get_puuid_challengers_queue(queue))

games = []
# ONE API CALL PER 100 GAMES PER PLAYER
for player in tqdm.tqdm(players_puuid):
    games.extend(get_solorankedgames_from_puuid(player, int(time.time()-12960000)))

print(len(games))
games = set(games)
print(len(games))