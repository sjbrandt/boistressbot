import re
import os

import discord
from discord import app_commands
from discord.ext import tasks

import users
import steam_api
import gener8rs_api
import teamwork_tf_api

# Settings
REFER_TO_OTHER_USERS_BY_MENTION = False

# Initialize
GUILD_ID = int(os.getenv('GUILD_ID'))
CREATOR_DISCORD_ID = int(os.getenv('CREATOR_DISCORD_ID'))
GENERAL_CHANNEL_ID = int(os.getenv('GENERAL_CHANNEL_ID'))
BOT_COMMANDS_CHANNEL_ID = int(os.getenv('BOT_COMMANDS_CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)

def verify():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel_id != BOT_COMMANDS_CHANNEL_ID:
            await interaction.response.send_message(
                f":point_right: <#{BOT_COMMANDS_CHANNEL_ID}>",
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)


# Commands
@verify()
@tree.command(
    name="hello",
    description="Social convention of acknowledgement",
    guild=discord.Object(id=GUILD_ID)
)
async def hello_command(interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}!")


@verify()
@tree.command(
    name="github",
    description="Get link to my GitHub repository!",
    guild=discord.Object(id=GUILD_ID)
)
async def github_command(interaction):
    await interaction.response.send_message("Here ya go!\nhttps://github.com/sofusbrandt/BoistressBot")


@verify()
@tree.command(
    name="playtime",
    description="Get the playtime for yourself or the given player",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    player="Player for which to get the class playtimes"
)
@app_commands.choices(player=[
    app_commands.Choice(name="Sofus", value="toastysauze"),
    app_commands.Choice(name="Gustav", value="mallow_opus"),
    app_commands.Choice(name="Philip", value="pvcolsen"),
    app_commands.Choice(name="Mathias", value="mathiasnova"),
    app_commands.Choice(name="Thorvald", value="mistralextra"),
    app_commands.Choice(name="Adrian", value="thewildcards")
])
async def playtime(interaction, player: app_commands.Choice[str] = None):
    playername = interaction.user.name if player is None else player.value

    if re.compile("<@[0-9]+>").match(playername):  # mention is used instead of username
        member = await interaction.guild.fetch_member(playername[2:-1])
        playername = member.name

    steam_id = users.steam_id_from_discord_username(playername)

    if steam_id is None:
        await interaction.response.send_message(f"User {playername} not found")
        return

    hours = int(steam_api.get_playtime(steam_id))

    player_reference = f"<@{playername}>" if REFER_TO_OTHER_USERS_BY_MENTION else playername
    await interaction.response.send_message(f"Player {player_reference} has played Team Fortress 2 for {hours} hours!")


@verify()
@tree.command(
    name="playtimes",
    description="Get the playtime for all players",
    guild=discord.Object(id=GUILD_ID)
)
async def playtimes(interaction):
    msg = "## Playtime of all players\n"
    
    for user in users.load_users():
        name = user['discord_username']
        playtime = user['registered_hours']
        msg += f"* **{name}**: {playtime} hrs\n"
    
    await interaction.response.send_message(msg)


@verify()
@tree.command(
    name="loadouts",
    description="Generate random loadouts for random classes",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(count="Amount of loadouts to generate. Leave blank for 6 named loadouts.")
async def loadouts(interaction, count: int = None):
    persons = ['Sofus', 'Adrian', 'Gustav', 'Philip', 'Thorvald', 'Mathias']
    message = "## Random loadouts\n"
    use_names = False

    if count is None:
        use_names = True
        count = 6

    fmsg = "people's" if use_names else count
    await interaction.response.send_message(f"Fetching {fmsg} loadouts...")

    for i in range(0, count):
        loadout = gener8rs_api.random_loadout()

        _class = loadout['_sChosenClass']
        primary = loadout['_sPrimary']
        secondary = loadout['_sSecondary']
        melee = loadout['_sMelee']
        building = loadout['_sBuilding']

        if use_names:
            message += f"__{persons[i]}__: **{_class}**\n"
        else:
            message += f"{i + 1}: **{_class}**\n"
        message += f"{primary}\n"
        message += f"{secondary}\n"
        message += f"{melee}\n"
        if building is not None:
            message += f"{building}\n"
        message += "\n"

    await interaction.edit_original_response(content=message)


@verify()
@tree.command(
    name="stathelp",
    description="Get list of available stats to fetch using the /stats command",
    guild=discord.Object(id=GUILD_ID)
)
async def stathelp(interaction):
    link = "https://github.com/sofusbrandt/BoistressBot/blob/dev/stats_list.txt"
    await interaction.response.send_message(f"[List of available stats for /stat]({link})")


@tree.command(
    name="stat",
    description="Get a given stat for a given player",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    stat="Stat name according to Steam API (see list with /stathelp)",
    playername="Discord username or @mention of the player, or blank to use yourself"
)
async def stat(interaction, stat: str, playername: str = None):
    if playername is None:
        playername = interaction.user.name

    if re.compile("<@[0-9]+>").match(playername):  # mention is used instead of username
        member = await interaction.guild.fetch_member(playername[2:-1])
        playername = member.name

    steam_id = users.steam_id_from_discord_username(playername)

    if steam_id is None:
        await interaction.response.send_message(f"User {playername} not found")
        return

    stat_result = steam_api.get_stat(steam_id, stat)

    if stat_result is None:
        await interaction.response.send_message(f"Stat {stat} for {playername} not found")

    await interaction.response.send_message(f"{playername} - `{stat}` = {stat_result}")


@verify()
@tree.command(
    name="comp-activity",
    description="Get amount of active games and players in valve competitive",
    guild=discord.Object(id=GUILD_ID)
)
async def compactivity(interaction, count: int = None):
    data = teamwork_tf_api.get_comp_activity()
    try:
        players = data['players']
        servers = data['servers_non_empty']
        date = data['created_at']

        await interaction.response.send_message(f"Valve competitive matchmaking currently has **{players} players** in **{servers} servers**\n_as of {date}_")
    except Exception as e:
        on_error(interaction, discord.app_commands.AppCommandError)


@verify()
@tree.command(
    name="classtimes",
    description="Get class playtimes for the given player",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    player="Player for which to get the class playtimes"
)
@app_commands.choices(player=[
    app_commands.Choice(name="Sofus", value="toastysauze"),
    app_commands.Choice(name="Gustav", value="mallow_opus"),
    app_commands.Choice(name="Philip", value="pvcolsen"),
    app_commands.Choice(name="Mathias", value="mathiasnova"),
    app_commands.Choice(name="Thorvald", value="mistralextra"),
    app_commands.Choice(name="Adrian", value="thewildcards")
])
async def classtimes(interaction, player: app_commands.Choice[str] = None):
    playername = interaction.user.name if player is None else player.value
    
    steam_id = users.steam_id_from_discord_username(playername)
    
    class_playtimes = steam_api.get_class_playtimes(steam_id)
    class_playtimes_sorted = dict(sorted(
        class_playtimes.items(),
        key=lambda item: item[1],
        reverse=True
    ))
    
    msg = f"## Class playtimes for {playername}\n"
    for _class in class_playtimes_sorted:
        msg += f"1. **{_class}** - {class_playtimes[_class]} hrs\n"
    
    await interaction.response.send_message(msg)


@tasks.loop(minutes=10)
async def update_player_playtimes():
    channel = await client.fetch_channel(GENERAL_CHANNEL_ID)
    for user in users.load_users():
        steam_id = user['steam_id']
        registered_playtime = users.get_registered_playtime(steam_id)
        actual_playtime = steam_api.get_playtime(steam_id)
        users.update_registered_playtime(steam_id, int(actual_playtime))

        if actual_playtime // 100 > registered_playtime // 100:
            reference = f"<@{user['discord_id']}>"
            broken_barrier = int((actual_playtime // 100) * 100)
            await channel.send(f"## {reference} just reached {broken_barrier} hours!")


# Error handling
@tree.error
async def on_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    # app_commands check failure, from verify() which has already responded
    if isinstance(error, discord.app_commands.CheckFailure):
        return
    message = "Whoops, I had an error! Let me call my boss for a second...\n\n"
    message += f"<@{CREATOR_DISCORD_ID}> hey dickface! ur a dumbfuck!\n\n"
    message += f"```{error}```"
    await interaction.channel.send(message)


# Events
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"{client.user} has connected to Discord!")
    update_player_playtimes.start()

# Run
# Taken from line 28-42 of https://replit.com/@replit/Python-Discord-Bot#main.py
try:
    token = os.getenv('DISCORD_TOKEN') or ''
    if token == '':
        raise Exception("Please add your token to the Secrets pane.")
    client.run(token)
except discord.HTTPException as e:
    if e.status == 429:
        print(
            "The Discord servers denied the connection for making too many requests"
        )
        print(
            "Get help from https://stackoverflow.com/questions/66724687/"
            + "in-discord-py-how-to-solve-the-error-for-toomanyrequests"
        )
    else:
        raise e
