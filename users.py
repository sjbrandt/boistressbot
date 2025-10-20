import json

from discord import app_commands


def steam_id_from_discord_username(discord_username: str):
    users = load_users()
    for user in users:
        if user['discord_username'] == discord_username:
            return user['steam_id']
    return None


def steam_id_from_discord_id(discord_id: str):
    users = load_users()
    for user in users:
        if user['discord_id'] == discord_id:
            return user['steam_id']
    return None


def load_users():
    f = open('data/users.json')
    users = json.load(f)
    return users


def save_users(users: dict[str, any]):
    json_object = json.dumps(users, indent=2)
    with open('data/users.json', 'w') as file:
        file.write(json_object)


def id_match(id_or_username: str | int, user: dict[str, any]) -> bool:
    accepted_ids = [
        user['discord_username'],
        user['discord_id'],
        user['steam_id']
    ]
    if id_or_username in accepted_ids:
        return True
    return False


def get_registered_playtime(id_or_username: int | str) -> int:
    users = load_users()
    for user in users:
        if id_match(id_or_username, user):
            return user['registered_hours']


def update_registered_playtime(id_or_username: int | str, hours: int):
    users = load_users()
    for user in users:
        if id_match(id_or_username, user):
            user['registered_hours'] = hours
    save_users(users)


def generate_choices():
    choices = []
    for user in load_users():
        choices.append(app_commands.Choice(name=user['name'], value=user['discord_username']))
    
    return choices


def generate_name_list():
    names = []
    for user in load_users():
        names.append(user['name'])
    return names
