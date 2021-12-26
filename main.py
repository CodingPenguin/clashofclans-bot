from discord.embeds import Embed
from env import API_KEY, PROXIES, TOKEN, MONGO_SRV_URL
import discord, requests, asyncio
from pymongo import MongoClient
from datetime import date
from loguru import logger

from discord.errors import HTTPException
from discord.ext import commands
from helpers.clan import fetch_clan_contents, save_clan_tag, send_clan_contents, set_default_clan
from helpers.constants import BH_HEROES, TH_HEROES
from helpers.graph import plot_trophy_graph, set_graph_embed

from helpers.stats import get_player_stats, get_stats_embed
from helpers.verify import set_verify_embed, write_to_db
from helpers.zap import set_zap_embed
from helpers.zapquake import set_zapquake_embed

intents = discord.Intents.default()
intents.members = True

mongo_client = MongoClient(MONGO_SRV_URL)
db = mongo_client.coc
col = db.users

client = commands.Bot(command_prefix='coc ', intents=intents, help_command=None)


@client.event
async def on_ready():
    logger.info(f'We have logged in as {client.user}')    
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(client.guilds)} servers"))
    
    
@client.event
async def on_message(message):   
    if message.author == client.user:
        return

    if message.content == "coc":
        logger.info('coc')
        couroutines = []
        couroutines.append(message.channel.send(
            f"Hello {message.author.name}! Did you know I'm on {len(client.guilds)} Discord servers? Also, there are {col.count_documents({})} verified users using me. I'm more popular than you!"
        ))
        couroutines.append(client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(client.guilds)} servers")))
        await asyncio.gather(*couroutines)
    
    await client.process_commands(message)


@client.command()
async def help(ctx):
    logger.info('help')
    
    embed_var = discord.Embed(
        title="Commands!", 
        description="Every command starts with the prefix \"coc\" followed by a space and the keyword.",
        color=0x000000
    )
    
    embed_var.add_field(name="`stats`", value="Retrieve's player's stats.\nEx: coc stats [player_tag]\nUNLESS you have already verified using coc verify, in which case:\ncoc stats.", inline=False)
    embed_var.add_field(name="`verify`", value="Verifies and authenticates you by matching up your Discord ID to your CoC player tag.\nFollow instructions in DMs.\nEx: coc verify", inline=False)
    embed_var.add_field(name="`graph`", value="Plots your trophy count daily.\nHas to be run manually each day, and can only retrieve new trophy counts each day.\nOnly available once you have verified using coc verify.\nEx: coc graph", inline=False)
    embed_var.add_field(name="`hero`", value="Lists your hero levels.\nTells how far you are from maxed hero levels at your Town Hall level.\nOnly available once you have verified using coc verify.\nEx: coc hero")
    embed_var.add_field(name="`zap`", value="Tells the player how many lightning spells are required to destroy an air defense.\nThis command requires two parameters: the air defense level and your lightning spell level.\nEx: coc zap [air defense level] [lightning spell level]", inline=False)
    embed_var.add_field(name="`zapquake`", value="Tells the player how many lightning and earthquake spells are required to destroy an air defense.\nThis command requires three parameters: the air defense level and a lightning spell level, and an earthquake spell level.\nEx: coc zapquake [air defense level] [lightning spell level] [earthquake spell level]", inline=False)
    embed_var.add_field(name="`help`", value="Sends this command list.", inline=False)
    embed_var.add_field(name="Contribute & Support", value="For further inquiries, contact me in Discord @ danmaruchi#8034.\nIf you are satisfied with this bot, leave a review on [Top.gg](https://top.gg/bot/870085172136149002)!\nAnd if you want to support me directly, [buy me a coffee](https://www.buymeacoffee.com/danmaruchi)!")
    
    await ctx.send(embed=embed_var)   
    
     
@client.command()
async def stats(ctx, tag: str=None):
    logger.info('stats')
    
    author_id = str(ctx.author.id)
    selector = {'_id': author_id}
    if (user := col.find_one(selector)) is not None:
        user_tag = user['player_tag']
    
    if user and tag is None:
        await ctx.send(embed=get_stats_embed(user_tag))
        return
    if tag is None:
        await ctx.send("Please enter a tag or run `coc verify` to use `coc stats` without entering a player tag.")
        return
    tag = tag.replace('#', "%23")
    await ctx.send(embed=get_stats_embed(tag))
    
    
@client.command()
async def verify(ctx):
    logger.info('verify')
    
    author_id = str(ctx.author.id)
    selector = {'_id': author_id}
    if col.find_one(selector) is not None:
        await ctx.send("You are already verified!")
        return

    def check(msg) -> bool:
        return msg.author == ctx.author and str(msg.channel.type) == "private"
    
    await ctx.author.send("Enter your in-game player tag followed by a space and then your player token!\nFor example: `#IN-GAME-PLAYERTAG apitoken`\nYour API token can be found in-game. Gear Icon -> More Settings -> Tap 'Show' to see API token")
    user_data = await client.wait_for("message", check=check)
    user_tag = user_data.content.split(' ')[0].replace('#', '%23')
    user_token = user_data.content.split(' ')[1]
    
    url = f'https://api.clashofclans.com/v1/players/{user_tag}/verifytoken'
    token_data = {
        'token': f'{user_token}'
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'authorization': f'Bearer {API_KEY}',
    }
    try:
        response = requests.post(
            url,
            json=token_data,
            headers=headers,
            proxies=PROXIES
        )
        response.raise_for_status()
    except HTTPException as e:
        print('error: ', e)
        await ctx.send("There was an error with the server. Please try again.")
        
    res = response.json()
    if 'status' in res:
        if res['status'] == 'ok':
            write_to_db(author_id, user_tag) # async 1
            embed_var = set_verify_embed(ctx.author.name) # async 2
            await ctx.send(embed=embed_var) # async 3
            await ctx.author.send("Verified!") # send verified in dm, async 4
        else:
            await ctx.author.send("Please try again by saying `coc verify` in the server. Check for typos.")
            
            
@client.command()
async def graph(ctx):
    logger.info('graph')
    
    author_id = str(ctx.author.id)
    selector = {'_id': author_id}
    if (user_data := col.find_one(selector)) is None:
        await ctx.send("Please verify by using `coc verify` to use `coc graph`")        
        return
    
    today = str(date.today().strftime('%b %d %y'))
    
    if today in user_data['trophy_data']: # graphs "today" graph and does not make a new graph. Just uses the info alr in database for "today"
        plot_trophy_graph(user_data['trophy_data'])
        file = discord.File("./graph.png", filename="graph.png")
        await ctx.send(file=file, embed=set_graph_embed(ctx.author.name))
        return
    
    tag = str(user_data['player_tag'])
    player_stats = get_player_stats(tag)
    current_trophy_count = str(player_stats['trophies'])
    col.update_one(
        {       
            '_id': author_id
        }, 
        {
            '$set': {
                f"trophy_data.{today}": current_trophy_count
            }
        }
    )
    user_data = col.find_one({'_id': author_id})
    plot_trophy_graph(user_data['trophy_data'])
    file = discord.File("./graph.png", filename="graph.png")
    await ctx.send(file=file, embed=set_graph_embed(ctx.author.name))
    

@client.command()
async def hero(ctx):
    logger.info('hero')
    
    author_id = str(ctx.author.id)
    selector = {'_id': author_id}
    if (user_data := col.find_one(selector)) is None:
        await ctx.send("Please verify by using `coc verify` to use `coc hero`")        
        return
    
    player_stats = get_player_stats(user_data['player_tag'])
    
    if 'townHallLevel' not in player_stats:
        await ctx.send('There was an error with the Clash of Clans API. Please try again later.')
        return
    if 'heroes' not in player_stats:
        await ctx.send('There was an error with the Clash of Clans API. Please try again later.')
        return
        
    hall_level = player_stats['townHallLevel']
    heroes = player_stats['heroes']
    
    if not len(heroes):
        await ctx.send("You don't have any heroes :(")
        return
    
    embed_var = discord.Embed(
      title=f"{player_stats['name']}'s Heroes",
      color=0x000000
    )
    
    for hero in heroes:
        HERO_DICT = TH_HEROES
        if hero['name'] == 'Barbarian King':
            hero_name = f"{hero['name']} 👑"
        elif hero['name'] == 'Archer Queen':
            hero_name = f"{hero['name']} 🏹"
        elif hero['name'] == 'Grand Warden':
            hero_name = f"{hero['name']} 🪄"
        elif hero['name'] == 'Royal Champion':
            hero_name = f"{hero['name']} 🔱"
        elif hero['name'] == 'Battle Machine':
            hero_name = f"{hero['name']} 🔨"
            HERO_DICT = BH_HEROES
            hall_level = player_stats['builderHallLevel']
        
        else:
            hero_name = hero['name']
        
        max_hero_level = HERO_DICT[hall_level][hero['name']]['max_level']
        maxed_percentage = round((hero["level"] / max_hero_level) * 100, 2)
        
        if (level_to_max := max_hero_level - hero['level']):
            time_to_max = HERO_DICT[hall_level][hero['name']]['max_time'][-level_to_max:]
            time_to_max = sum(time_to_max) / 24
            embed_value = f"Level {hero['level']} ({maxed_percentage}%)\nYour {hero['name']} is {level_to_max} level(s) away from maxed.\nOnly {time_to_max} days left to go."
        else:
            embed_value = f"Level {hero['level']} ({maxed_percentage}%)\nYour {hero['name']} is maxed.\nThat's some dedication!"
            
        embed_var.add_field(
            name=hero_name,
            value=embed_value,
            inline=False
        )
        
    await ctx.send(embed=embed_var)
    

@client.command()
async def clan(ctx, clan_tag: str=''):
    logger.info('clan')
    author_id = str(ctx.author.id)
    selector = {'_id': author_id}
    projection = {'clan_tag': 1}
    if (user_data := col.find_one(selector, projection)) is None:
        await ctx.send("Please verify by using `coc verify` to use `coc clan`")        
        return
    
    if clan_tag == '' and 'clan_tag' in user_data:
        clan_tag = user_data['clan_tag']
        contents = await fetch_clan_contents(clan_tag)
    elif len(clan_tag):
        try:
            contents = await set_default_clan(client, ctx, clan_tag, author_id)  
        except Exception as e:
            await ctx.send(e)
    else:
        error_embed = Embed(title='Input Error', description='Please enter a clan tag!', color=0xFF0000)
        await ctx.send(embed=error_embed)
    
    try:
        await send_clan_contents(client, ctx, contents)
    except Exception as e:
        logger.error(f'ERROR: {e}')
        await ctx.send('There was an internal error. Please try again later.')
        
        
@client.command()
async def zap(ctx, airdef="0", zap="0"):
    logger.info('zap')
    
    try:
        airdef = int(airdef)
        zap = int(zap)
    except Exception:
        await ctx.send("Please enter valid air defense and/or lightning spell levels. You didn't put in numbers.")
        
    if (airdef < 1 or airdef > 12) or (zap < 1 or zap > 9):
        await ctx.send("Please enter valid air defense and/or lightning spell levels. Ex: coc zap [air defense level] [lightning spell level]")
        return
    
    embed_var = await set_zap_embed(airdef, zap)
    await ctx.send(embed=embed_var)
    
    
@client.command()
async def zapquake(ctx, airdef="0", zap="0", quake="0"):
    logger.info('zapquake')
    try:
        airdef = int(airdef)
        zap = int(zap)
        quake = int(quake)
    except Exception:
        await ctx.send("Please enter valid air defense, lightning spell, and/or earthquake spell levels. You didn't put in numbers.")
        
    if (airdef < 1 or airdef > 12) or (zap < 1 or zap > 9) or (quake < 1 or quake > 5):
        await ctx.send("Please enter valid air defense, lightning spell levels, and/or earthquake spell levels. Ex: coc zapquake [air defense level] [lightning spell level] [earthquake spell level]")
        return
    
    embed_var = await set_zapquake_embed(airdef, zap, quake)
    await ctx.send(embed=embed_var)


if __name__ == '__main__':
    client.run(TOKEN)

