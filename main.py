
from time import time
import discord, requests, pymongo
import os
import matplotlib.pyplot as plt
from datetime import date

from discord.errors import HTTPException
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
    
# heroku prod and local

API_KEY = os.environ["API_KEY"]
TOKEN = os.environ["TOKEN"]
proxies = {
    "http": os.environ['QUOTAGUARDSTATIC_URL'],
    "https": os.environ['QUOTAGUARDSTATIC_URL']
}
mongo_client = pymongo.MongoClient(f"mongodb+srv://danmaruchiAdmin:{os.environ['MONGO_PASSWORD']}@cluster0.hbcfw.mongodb.net/cocstatsbot?retryWrites=true&w=majority")
db = mongo_client.coc
col = db.users
    
    
client = commands.Bot(command_prefix='coc ', intents=intents)

# HELPERS:
def get_player_stats(tag):
    url = f'https://api.clashofclans.com/v1/players/{tag}'
    headers = {
        'Accept': 'application/json',
        'authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers, proxies=proxies)
        response.raise_for_status()
    except:
        return "There was an error with the request. Please try again later."
    
    res = response.json()
    return res

# BEGIN COC STATS HELPERS
def get_stats_embed(tag):
    data = get_player_stats(tag)
    return(set_stats_embed(data["name"], data["clan"]["name"], data["clan"]["tag"], data["trophies"], data["warStars"]))
        

def set_stats_embed(name, clan, clan_tag, trophies, war_stars):
    embed_var = discord.Embed(title=f"{name}'s Stats", color=0xD40C00)
    embed_var.add_field(name="Clan ⚔️", value=f"{clan} ({clan_tag})", inline=False)
    embed_var.add_field(name="Trophies 🏆", value=f"{trophies}", inline=False)
    embed_var.add_field(name="War Stars ⭐", value=f"{war_stars}", inline=False)
    
    return(embed_var)


# BEGIN COC VERIFY HELPERS
def set_verify_embed(author_name):
    embed_var = discord.Embed(
        title="Success! ✅",
        description=f"**{author_name}** has been verified!",
        color=0x32C12C
    )
    return embed_var

def write_to_db(author_id, tag):
    new_user_data = {
        "_id": str(author_id),
        'player_tag': str(tag),
        'trophy_data': {
            
        }
    }
    col.insert_one(new_user_data)


# END COC VERIFY HELPERS
# BEGIN COC GRAPH HELPERS
def plot_trophy_graph(data):
    dates = list(data.keys())
    trophy_values = list(map(int, list(data.values())))
    
    plt.figure(facecolor="#2F3136")
    plt.plot(dates, trophy_values, marker='o', color='white') 
    plt.tight_layout()
    plt.text(dates[-1], trophy_values[-1], f'{trophy_values[-1]}   ', horizontalalignment='right', color="white")
    
    ax = plt.gca()
    ax.set_facecolor(('#2F3136'))
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('#2F3136') 
    ax.spines['right'].set_color('#2F3136')
    ax.spines['left'].set_color('white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
        
    plt.savefig('graph.png')
    plt.clf()

def set_graph_embed(author_name):
    embed_var = discord.Embed(
        title=f"**{author_name}** Trophy Graph",
        description="All-time Graph",
        color=0x000000
    )
    embed_var.set_image(url="attachment://graph.png")
    return embed_var
# END COC GRAPH HELPERS
    
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    
@client.event
async def on_message(message):   
    if message.author == client.user:
        return
    
    if message.content == "coc":
        await message.channel.send(f"Hello {message.author.name}!")
    await client.process_commands(message)
    
@client.command()
async def stats(ctx, tag="0"):
    check_verified = col.count_documents({'_id': str(ctx.author.id)}, limit=1)
    user_tag = col.find_one({
        '_id': str(ctx.author.id)
    })['player_tag']
    
    if check_verified and tag == "0":
        await ctx.send(embed=get_stats_embed(user_tag))
        return
    if tag == "0":
        await ctx.send("Please enter a tag or run `coc verify` to use `coc stats` without entering a player tag. ")
        return
    tag = tag.replace('#', "%23")
    await ctx.send(embed=get_stats_embed(tag))

@client.command()
async def verify(ctx):
    check_verified = col.count_documents({'_id': str(ctx.author.id)}, limit=1)
    if check_verified:
        await ctx.send("You are already verified!")
        return

    def check(msg):
        return msg.author == ctx.author and str(msg.channel.type) == "private"
    
    await ctx.author.send("Enter your player tag followed by a space and then your player token!\nFor example: `#PLAYERTAG apitoken`\nYour API token can be found in-game. Gear Icon -> More Settings -> Tap 'Show' to see API token")
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
            proxies=proxies
        )
        response.raise_for_status()
    except HTTPException as e:
        print('error: ', e)
        
        
    res = response.json()
    if 'status' in res:
        if res['status'] == 'ok':
            guild = client.get_guild(ctx.guild.id) # Get Guild w/ Guild ID
            role = discord.utils.get(guild.roles, name="verified player") # Get Role w/ Role ID
            member = guild.get_member(ctx.author.id) # Get member by author Id
            await member.add_roles(role)
            
            write_to_db(ctx.author.id, user_tag)
            
            embed_var = set_verify_embed(ctx.author.name)
            await ctx.send(embed=embed_var)
            await ctx.author.send("Verified!") # send verified in dm
        else:
            await ctx.author.send("Please try again by saying `coc verify` in the server. Check for typos.")
@client.command()
async def graph(ctx):
    check_verified = col.count_documents({'_id': str(ctx.author.id)}, limit=1)
    if check_verified == 0:
        await ctx.send("Please verify by using `coc verify` to use `coc graph`")
        return
    
    author_id = str(ctx.author.id)
    today = str(date.today().strftime('%b %d %y'))
    
    user_data = col.find_one({'_id': author_id})
    print(user_data)
    
    
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
            '$set' : {
                f"trophy_data.{today}": f"{current_trophy_count}"
            }
        }
    )
    print(user_data)
    print(user_data['trophy_data'])
    
    plot_trophy_graph(user_data['trophy_data'])
    
    file = discord.File("./graph.png", filename="graph.png")
    await ctx.send(file=file, embed=set_graph_embed(ctx.author.name))

# async def help(ctx):
#     msg = """
#     ```
    
#     ```
#     """
#     await ctx.send()

client.run(TOKEN)


