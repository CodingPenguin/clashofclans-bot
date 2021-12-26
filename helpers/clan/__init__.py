import requests, json, asyncio
from env import API_KEY, PROXIES, MONGO_SRV_URL

from loguru import logger
from pydantic import ValidationError
from pymongo import MongoClient

from discord import Embed
from discord.errors import ClientException, HTTPException

from helpers.clan.helpers.general import fetch_general_clan_stats
from helpers.clan.helpers.leaderboard import fetch_leaderboard
from helpers.clan.helpers.member import fetch_member_stats

from helpers.clan.models import ClanBase


async def fetch_clan_stats(clan_tag: str):
    if clan_tag.startswith('#'):
        clan_tag = clan_tag.replace('#', '%23')
    elif not clan_tag.startswith('%23'):
        raise ClientException('Please enter a valid clan tag.')
    
    url = f'https://api.clashofclans.com/v1/clans/{clan_tag}'
    headers = {
        'Accept': 'application/json',
        'authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers, proxies=PROXIES)
    response.raise_for_status()
    res = response.json()
    res = ClanBase(**res)
    
    return json.loads(res.json())


async def fetch_clan_contents(clan_tag):
    try:
        clan_stats = await fetch_clan_stats(clan_tag)
    except HTTPException as e:
        logger.error(f'ERROR: {e}')
        raise HTTPException('There was an error with the Clash of Clans API, or invalid clan tag. Please try again later.')
    except ValidationError as e:
        logger.error(f'ERROR: {e}')
        raise ValidationError('Clash of Clans API is provided invalid response. Please try again later.')
    except ClientException as e:
        logger.error(f'ERROR: {e}')
        raise ClientException(e)
    
    contents = []
    contents.append(fetch_general_clan_stats(clan_stats))
    contents.append(fetch_member_stats(clan_stats))
    contents.append(fetch_leaderboard(clan_stats))
    
    try:
        contents = await asyncio.gather(*contents)
        leaderboards = contents.pop(2)
        contents.extend(leaderboards)
    except Exception as e:
        logger.error(f'ERROR: {e}')
        
    return contents
    
    
async def save_clan_tag(user_id: str, clan_tag: str):
    mongo_client = MongoClient(MONGO_SRV_URL)
    db = mongo_client.coc
    users = db.users
    
    clan_tag = clan_tag.replace('#', '%23')
    try:
        users.update_one({'_id': user_id}, {
            '$set': {
                'clan_tag': clan_tag
            }
        })
    except Exception as e:
        logger.error(f'ERROR: {e}')
        raise Exception('There was a database error. Clan was not saved as default clan.')
    
    
async def set_default_clan(client, ctx, clan_tag, author_id):    
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['✅', '❌']
    
    try:
        contents = await fetch_clan_contents(clan_tag)
    except Exception as e:
        raise Exception('An error occurred. Assure you have a valid clan tag, though it may be an issue with Clash of Clans API. Please try again.')
    
    save_embed = Embed(
        title='Default Clan?',
        description='Would you like to save this clan as your default clan?',
        color=0x000000
    )
    message = await ctx.send(embed=save_embed)
    await message.add_reaction('✅')
    await message.add_reaction('❌')
    
    while True:
        try:
            reaction, user = await client.wait_for("reaction_add", timeout=120, check=check)
            if str(reaction.emoji) == '✅':
                try:
                    await save_clan_tag(author_id, clan_tag)
                    saved_embed = Embed(
                        title="Success! ✅",
                        description=f"Clan {clan_tag} has been set as your default clan!\nYou can now use `coc clan` without a clan tag.\nTo update your clan, use `coc clan <new clan tag>`",
                        color=0x32C12C
                    )
                    await ctx.send(embed=saved_embed)
                    await message.delete()
                    break
                except Exception as e:
                    await ctx.send(e)
                    await message.delete()
                    break
            elif str(reaction.emoji) == '❌':
                not_saved_embed = Embed(
                    title="Not saved! ✅",
                    description=f"Clan {clan_tag} has NOT been set as your default clan.",
                    color=0x32C12C
                )
                await ctx.send(embed=not_saved_embed)
                await message.delete()
                break
            else:
                message.remove_reaction(reaction, user)
        except asyncio.TimeoutError:
            await message.delete()
            break
    return contents


async def send_clan_contents(client, ctx, contents):
    pages = len(contents)
    cur_page = 1
    for idx, content in enumerate(contents):
        content.set_footer(text=f'page {idx+1}/{pages}')
    message = await ctx.send(embed=contents[cur_page-1])
    await message.add_reaction("◀️")
    await message.add_reaction("▶️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['◀️', '▶️']
        
    while True:
        try:
            reaction, user = await client.wait_for("reaction_add", timeout=120, check=check)

            if str(reaction.emoji) == "▶️" and cur_page != pages:
                cur_page += 1
                await message.edit(embed=contents[cur_page-1])
                await message.remove_reaction(reaction, user)
                
            elif str(reaction.emoji) == "◀️" and cur_page > 1:
                cur_page -= 1
                await message.edit(embed=contents[cur_page-1])
                await message.remove_reaction(reaction, user)
                
            else:
                await message.remove_reaction(reaction, user)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            break