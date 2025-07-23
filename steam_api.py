import os
import requests
import re

KEY = os.getenv('STEAM_API_KEY')


def get_playtime(steam_id: str):
    url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    args = f"?key={KEY}&steamid={steam_id}&format=json&include_appinfo=true&include_played_free_games=true"
    response = requests.get(url + args)
    data = response.json()

    games = data['response']['games']
    for game in games:
        if game['appid'] == 440:
            playtime = game['playtime_forever'] / 60
            return playtime

    return None


def get_stat(steam_id: str, stat: str):
    url = f"https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/?appid=440&key={KEY}&steamid={steam_id}&format=json"
    response = requests.get(url)
    data = response.json()

    for stat_object in data['playerstats']['stats']:
        if stat_object['name'] == stat:
            return stat_object['value']

    return None


def get_class_playtimes(steam_id: str) -> dict[str, int]:
    url = f"https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/?appid=440&key={KEY}&steamid={steam_id}&format=json"
    response = requests.get(url)
    data = response.json()
    
    results = {
        'Scout': -1,
        'Soldier': -1,
        'Pyro': -1,
        'Demoman': -1,
        'Heavy': -1,
        'Engineer': -1,
        'Medic': -1,
        'Sniper': -1,
        'Spy': -1
    }
    
    for stat in data['playerstats']['stats']:
        # match "<class>.accum.iPlayTime"
        match = re.match(r"(.+)\.accum\.iPlayTime$", stat['name'])
        if match:
            prefix = match.group(1)
            if prefix in results.keys():
                seconds = stat['value']
                hours = int(seconds / (60*60))
                results[prefix] = hours
    
    return results


def generate_stats_list(steam_id: str):
    url = f"https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/?appid=440&key={KEY}&steamid={steam_id}&format=json"
    response = requests.get(url)
    data = response.json()

    message = ""
    for stat in data['playerstats']['stats']:
        message += f"{stat['name']}\n"

    with open('stats_list.txt', 'w') as f:
        f.write(message)
