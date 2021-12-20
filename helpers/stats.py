import requests, discord
from env import API_KEY, PROXIES
from loguru import logger


def get_player_stats(tag: str):
    url = f'https://api.clashofclans.com/v1/players/{tag}'
    headers = {
        'Accept': 'application/json',
        'authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, proxies=PROXIES)
        response.raise_for_status()
        print(response.status_code)
    except Exception as e:
        logger.error(f'ERROR: {e}')
        return None
    
    res = response.json()
    return res


def get_stats_embed(tag: str) -> discord.Embed:
    data = get_player_stats(tag)
    if data is None:
        embed_var = discord.Embed(
            title='Request Error',
            description="There was an error with the request. Please try again later.",
            color=0xFF0000
        )
        return embed_var
    
    embed_data = {
      'player_name': data['name'],
      'clan_name': data['clan']['name'],
      'clan_tag': data['clan']['tag'],
      'donations': data['donations'],
      'donations_received': data['donationsReceived'],
      'trophies': data['trophies'],
      'war_stars': data['warStars']
    }
    embed = set_stats_embed(embed_data) 
    return embed
        

def set_stats_embed(embed_data: dict[str]) -> discord.Embed:
    embed_var = discord.Embed(
      title=f"{embed_data['player_name']}'s Stats",
      color=0xD40C00
    )
    embed_var.add_field(
        name="Clan ⚔️",
        value=f"{embed_data['clan_name']} ({embed_data['clan_tag']})",
        inline=False
    )
    embed_var.add_field(
        name="Donation Ratio 🤲",
        value=f"{round(embed_data['donations']/embed_data['donations_received'], 3)} ({embed_data['donations']}/{embed_data['donations_received']})",
        inline=False
    )
    embed_var.add_field(
        name="Trophies 🏆",
        value=f"{embed_data['trophies']}",
        inline=False
    )
    embed_var.add_field(
        name="War Stars ⭐",
        value=f"{embed_data['war_stars']}",
        inline=False
    )
    return embed_var
