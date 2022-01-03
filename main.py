import discord, requests, asyncio
from env import API_KEY, PROXIES, TOKEN, MONGO_SRV_URL, GUILD_IDS

from pymongo import MongoClient
from datetime import date
from loguru import logger

from discord.embeds import Embed
from discord.errors import HTTPException
from discord.ext import commands
from discord import Client, Intents, Embed
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option

from helpers.constants import BH_HEROES, TH_HEROES
from helpers.graph import plot_trophy_graph, set_graph_embed
from helpers.stats import get_player_stats, get_stats_embed
from helpers.verify import set_verify_embed, write_to_db
from helpers.clan import fetch_clan_contents, send_clan_contents, set_default_clan
from helpers.zap import set_zap_embed
from helpers.zapquake import set_zapquake_embed

mongo_client = MongoClient(MONGO_SRV_URL)
db = mongo_client.coc
col = db.users

bot = commands.Bot(command_prefix='coc ',intents=Intents.default(), help_command=None)
slash = SlashCommand(bot, sync_commands=True)


@slash.slash(name="coc", description='Greets you.')
async def _coc(ctx: SlashContext):
    logger.info('coc')

    embed = Embed(
        title='ClashStats',
        description=f"Hello {ctx.author.name}!\nDid you know I'm on **{len(bot.guilds)}** Discord servers?\nAlso, there are **{col.count_documents({})}** verified users using me. I'm more popular than you!",
    )
    
    await ctx.send(embed=embed)
    # await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} servers"))
    
    
@slash.slash(name='help', description='Displays the command list.')
async def _help(ctx: SlashContext):
    logger.info('help')
    
    help_contents = []
    help0 = Embed(
        title="Commands!", 
        description="Every command starts with the prefix \"coc\" followed by a space and the keyword.",
        color=0x000000
    )
    
    help0.add_field(name="`verify`", value="Verifies and authenticates you by matching up your Discord ID to your CoC player tag. Many of the following commands require verification before use.\nFollow instructions in DMs.\nEx: coc verify", inline=False)
    help0.add_field(name="`clan`", value="Retrieve's clan stats. Currently, the most comprehensive ClashStats has available.\nOnly available once you have verified using coc verify.\nEx: coc clan [clan_tag]\nUNLESS you set up your default clan already:\nEx: coc clan", inline=False)
    help0.add_field(name="`stats`", value="Retrieve's player's stats.\nEx: coc stats [player_tag]\nUNLESS you have already verified using coc verify, in which case:\ncoc stats.", inline=False)
    help0.add_field(name="`graph`", value="Plots your trophy count daily.\nHas to be run manually each day, and can only retrieve new trophy counts each day.\nOnly available once you have verified using coc verify.\nEx: coc graph", inline=False)
    
    help1 = Embed(
        title="Commands!", 
        description="Every command starts with the prefix \"coc\" followed by a space and the keyword.",
        color=0x000000
    )
    help1.add_field(name="`hero`", value="Lists your hero levels.\nTells how far you are from maxed hero levels at your Town Hall level.\nOnly available once you have verified using coc verify.\nEx: coc hero", inline=False)
    help1.add_field(name="`zap`", value="Tells the player how many lightning spells are required to destroy an air defense.\nThis command requires two parameters: the air defense level and your lightning spell level.\nEx: coc zap [air defense level] [lightning spell level]", inline=False)
    help1.add_field(name="`zapquake`", value="Tells the player how many lightning and earthquake spells are required to destroy an air defense.\nThis command requires three parameters: the air defense level and a lightning spell level, and an earthquake spell level.\nEx: coc zapquake [air defense level] [lightning spell level] [earthquake spell level]", inline=False)
    help1.add_field(name='`invite`', value="Fetches the permanent ClashStats Discord invite link.", inline=False)
    help1.add_field(name="`help`", value="Sends this command list.", inline=False)
    
    help2 = Embed(
        title="Contribute & Support", 
        color=0x000000
    )
    help2.add_field(name="Questions", value="Contact me in Discord @ danmaruchi#8034, or join the support server [here](https://discord.gg/6MXVXxK7pb).", inline=False)
    help2.add_field(name="Leave a review & vote", value="If you found ClashStats helpful in any way, leave a review or simply vote for ClashStats on [Top.gg](https://top.gg/bot/870085172136149002)! It takes less than a minute, and helps push out ClashStats to more players.", inline=False)
    help2.add_field(name="Donate", value="And if you want to support me directly, consider [buying me a coffee](https://www.buymeacoffee.com/danmaruchi). I'm a broke college student, so anything helps.", inline=False)
    
    help_contents.append(help0)
    help_contents.append(help1)
    help_contents.append(help2)
    
    pages = len(help_contents)
    cur_page = 1
    for idx, content in enumerate(help_contents):
        content.set_footer(text=f'Want to invite me? Run coc invite to get my invite link!\npage {idx+1}/{pages}')
    message = await ctx.send(embed=help_contents[cur_page-1])
    await message.add_reaction("◀️")
    await message.add_reaction("▶️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['◀️', '▶️']
        
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=120, check=check)

            if str(reaction.emoji) == "▶️" and cur_page != pages:
                cur_page += 1
                await message.edit(embed=help_contents[cur_page-1])
                await message.remove_reaction(reaction, user)
                
            elif str(reaction.emoji) == "◀️" and cur_page > 1:
                cur_page -= 1
                await message.edit(embed=help_contents[cur_page-1])
                await message.remove_reaction(reaction, user)
                
            else:
                await message.remove_reaction(reaction, user)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            break   
        

@slash.slash(name='invite', description='Get the ClashStats invite link.')
async def _invite(ctx: SlashContext):
    logger.info('invite')
    invite_embed = Embed(
        title="Invite me to your server!",
        description="[ClashStats Invite Link](https://discord.com/api/oauth2/authorize?client_id=870085172136149002&permissions=414464658496&scope=bot%20applications.commands)",
        color=0x000000
    )
    await ctx.send(embed=invite_embed)
    
    
@slash.slash(
    name='stats',
    description='Get player stats.',
    options=[
        create_option(
            name='tag',
            description='Your player tag',
            option_type=3,
            required=False
        )
    ]
)
async def _stats(ctx: SlashContext, tag: str=None):
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
    
    
@slash.slash(name='verify', description='Link your Discord profile to your Clash of Clans account.')
async def _verify(ctx: SlashContext):
    logger.info('verify')
    
    author_id = str(ctx.author.id)
    selector = {'_id': author_id}
    if col.find_one(selector) is not None:
        await ctx.send("You are already verified!")
        return

    def check(msg) -> bool:
        return msg.author == ctx.author and str(msg.channel.type) == "private"

    await ctx.author.send("Enter your in-game player tag followed by a space and then your player token!\nFor example: `#IN-GAME-PLAYERTAG apitoken`\nYour API token can be found in-game. Gear Icon -> More Settings -> Tap 'Show' to see API token")
    user_data = await bot.wait_for("message", check=check)
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
        elif res['status'] == 'invalid':
            await ctx.author.send("Please try again by saying `coc verify` in the server. Check for typos.")
    elif 'status' not in res:
        await ctx.author.send("There was an error with the Clash of Clans API. Please try again later, or report this issue in the support server.")
            
@slash.slash(name='graph', description='Graphs your daily trophy count.')
async def _graph(ctx: SlashContext):
    logger.info('graph')
    
    author_id = str(ctx.author.id)
    selector = {'_id': author_id}
    if (user_data := col.find_one(selector)) is None:
        remind_embed = Embed(
            title="Verification Required",
            description="Please verify by running `coc verify` to run `coc graph`"
        )
        await ctx.send(embed=remind_embed)        
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
    
    
@slash.slash(name='hero', description='Get your hero stats.')
async def _hero(ctx):
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

@slash.slash(
    name='clan',
    description='Get clan stats.',
    options=[
        create_option(
            name='clan_tag',
            description='Clan tag',
            option_type=3,
            required=False,
        )
    ]
)
async def _clan(ctx, clan_tag: str=''):
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
            contents = await set_default_clan(bot, ctx, clan_tag, author_id)  
        except Exception as e:
            await ctx.send(e)
    else:
        error_embed = Embed(title='Input Error', description='Please enter a clan tag!', color=0xFF0000)
        await ctx.send(embed=error_embed)
    
    try:
        await send_clan_contents(bot, ctx, contents)
    except Exception as e:
        logger.error(f'ERROR: {e}')
        
        
@slash.slash(
    name='zap',
    description='Check how many lightning spells it takes to destroy an air defense.',
    options=[
        create_option(
            name='airdef',
            description='Air Defense Level',
            option_type=4,
            required=True
        ),
        create_option(
            name='zap',
            description='Lightning Spell Level',
            option_type=4,
            required=True
        )
    ]
)
async def _zap(ctx: SlashContext, airdef, zap):
    logger.info('zap')
    
    airdef = int(airdef)
    zap = int(zap)
        
    if (airdef < 1 or airdef > 12) or (zap < 1 or zap > 9):
        await ctx.send("Please enter valid air defense and/or lightning spell levels. Ex: coc zap [air defense level] [lightning spell level]")
        return
    
    embed_var = await set_zap_embed(airdef, zap)
    await ctx.send(embed=embed_var)
    

@slash.slash(
    name='zapquake',
    description='Check how many lightning and earthquake spells it takes to destroy an air defense.',
    options=[
        create_option(
            name='airdef',
            description='Air Defense Level',
            option_type=4,
            required=True
        ),
        create_option(
            name='zap',
            description='Lightning Spell Level',
            option_type=4,
            required=True
        ),
        create_option(
            name='quake',
            description='Earthquake Spell Level',
            option_type=4,
            required=True
        )        
    ]
)
async def _zapquake(ctx: SlashContext, airdef, zap, quake):
    logger.info('zapquake')
    
    airdef = int(airdef)
    zap = int(zap)
    quake = int(quake)
        
    if (airdef < 1 or airdef > 12) or (zap < 1 or zap > 9) or (quake < 1 or quake > 5):
        await ctx.send("Please enter valid air defense, lightning spell levels, and/or earthquake spell levels. Ex: coc zapquake [air defense level] [lightning spell level] [earthquake spell level]")
        return
    
    embed_var = await set_zapquake_embed(airdef, zap, quake)
    await ctx.send(embed=embed_var)
    

@bot.event
async def on_ready():
    logger.info(f'We have logged in as {bot.user}')    
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="coc help"))
    
    
@bot.event
async def on_message(message):   
    if message.author == bot.user:
        return

    if message.content == "coc":
        logger.info('coc')
        coroutines = []
        coc_embed = Embed(
            title="ClashStats",
            description=f"Hello {message.author.name}!\nDid you know I'm on **{len(bot.guilds)}** Discord servers?\nAlso, there are **{col.count_documents({})}** verified users using me. I'm more popular than you!",
            color=0x000000
        )
        coroutines.append(message.channel.send(
            embed=coc_embed
        ))
        # coroutines.append(bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} servers")))
        await asyncio.gather(*coroutines)
    
    await bot.process_commands(message)


@bot.command()
async def help(ctx):
    logger.info('help')
    
    help_contents = []
    help0 = Embed(
        title="Commands!", 
        description="Every command starts with the prefix \"coc\" followed by a space and the keyword.",
        color=0x000000
    )
    
    help0.add_field(name="`verify`", value="Verifies and authenticates you by matching up your Discord ID to your CoC player tag. Many of the following commands require verification before use.\nFollow instructions in DMs.\nEx: coc verify", inline=False)
    help0.add_field(name="`clan`", value="Retrieve's clan stats. Currently, the most comprehensive ClashStats has available.\nOnly available once you have verified using coc verify.\nEx: coc clan [clan_tag]\nUNLESS you set up your default clan already:\nEx: coc clan", inline=False)
    help0.add_field(name="`stats`", value="Retrieve's player's stats.\nEx: coc stats [player_tag]\nUNLESS you have already verified using coc verify, in which case:\ncoc stats.", inline=False)
    help0.add_field(name="`graph`", value="Plots your trophy count daily.\nHas to be run manually each day, and can only retrieve new trophy counts each day.\nOnly available once you have verified using coc verify.\nEx: coc graph", inline=False)
    
    help1 = Embed(
        title="Commands!", 
        description="Every command starts with the prefix \"coc\" followed by a space and the keyword.",
        color=0x000000
    )
    help1.add_field(name="`hero`", value="Lists your hero levels.\nTells how far you are from maxed hero levels at your Town Hall level.\nOnly available once you have verified using coc verify.\nEx: coc hero", inline=False)
    help1.add_field(name="`zap`", value="Tells the player how many lightning spells are required to destroy an air defense.\nThis command requires two parameters: the air defense level and your lightning spell level.\nEx: coc zap [air defense level] [lightning spell level]", inline=False)
    help1.add_field(name="`zapquake`", value="Tells the player how many lightning and earthquake spells are required to destroy an air defense.\nThis command requires three parameters: the air defense level and a lightning spell level, and an earthquake spell level.\nEx: coc zapquake [air defense level] [lightning spell level] [earthquake spell level]", inline=False)
    help1.add_field(name='`invite`', value="Fetches the permanent ClashStats Discord invite link.", inline=False)
    help1.add_field(name="`help`", value="Sends this command list.", inline=False)
    
    help2 = Embed(
        title="Contribute & Support", 
        color=0x000000
    )
    help2.add_field(name="Questions", value="Contact me in Discord @ danmaruchi#8034, or join the support server [here](https://discord.gg/6MXVXxK7pb).", inline=False)
    help2.add_field(name="Leave a review & vote", value="If you found ClashStats helpful in any way, leave a review or simply vote for ClashStats on [Top.gg](https://top.gg/bot/870085172136149002)! It takes less than a minute, and helps push out ClashStats to more players.", inline=False)
    help2.add_field(name="Donate", value="And if you want to support me directly, consider [buying me a coffee](https://www.buymeacoffee.com/danmaruchi). I'm a broke college student, so anything helps.", inline=False)
    
    help_contents.append(help0)
    help_contents.append(help1)
    help_contents.append(help2)
    
    pages = len(help_contents)
    cur_page = 1
    for idx, content in enumerate(help_contents):
        content.set_footer(text=f'Want to invite me? Run coc invite to get my invite link!\npage {idx+1}/{pages}')
    message = await ctx.send(embed=help_contents[cur_page-1])
    await message.add_reaction("◀️")
    await message.add_reaction("▶️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['◀️', '▶️']
        
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=120, check=check)

            if str(reaction.emoji) == "▶️" and cur_page != pages:
                cur_page += 1
                await message.edit(embed=help_contents[cur_page-1])
                await message.remove_reaction(reaction, user)
                
            elif str(reaction.emoji) == "◀️" and cur_page > 1:
                cur_page -= 1
                await message.edit(embed=help_contents[cur_page-1])
                await message.remove_reaction(reaction, user)
                
            else:
                await message.remove_reaction(reaction, user)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            break   
     
     

@bot.command()
async def invite(ctx):
    logger.info('invite')
    invite_embed = Embed(
        title="Invite me to your server!",
        description="[ClashStats Invite Link](https://discord.com/api/oauth2/authorize?client_id=870085172136149002&permissions=414464658496&scope=bot%20applications.commands)",
        color=0x000000
    )
    await ctx.send(embed=invite_embed)
    
    
@bot.command()
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
    
    
@bot.command()
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
    user_data = await bot.wait_for("message", check=check)
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
        elif res['status'] == 'invalid':
            await ctx.author.send("Please try again by saying `coc verify` in the server. Check for typos.")
    elif 'status' not in res:
        await ctx.author.send("There was an error with the Clash of Clans API. Please try again later, or report this issue in the support server.")
            
@bot.command()
async def graph(ctx):
    logger.info('graph')
    
    author_id = str(ctx.author.id)
    selector = {'_id': author_id}
    if (user_data := col.find_one(selector)) is None:
        remind_embed = Embed(
            title="Verification Required",
            description="Please verify by running `coc verify` to run `coc graph`"
        )
        await ctx.send(embed=remind_embed)        
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
    

@bot.command()
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
    

@bot.command()
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
            contents = await set_default_clan(bot, ctx, clan_tag, author_id)  
        except Exception as e:
            await ctx.send(e)
    else:
        error_embed = Embed(title='Input Error', description='Please enter a clan tag!', color=0xFF0000)
        await ctx.send(embed=error_embed)
    
    try:
        await send_clan_contents(bot, ctx, contents)
    except Exception as e:
        logger.error(f'ERROR: {e}')
        
        
@bot.command()
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
    
    
@bot.command()
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
    bot.run(TOKEN)
