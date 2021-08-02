
from time import time
import discord, requests, json
import os
import matplotlib.pyplot as plt
from datetime import date

from discord.errors import HTTPException
from discord.ext import commands
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.members = True

if 'API_KEY' not in os.environ or 'TOKEN' not in os.environ: # local
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    TOKEN = os.getenv("TOKEN")
    proxies = {}
else: # heroku
    API_KEY = os.environ["API_KEY"]
    TOKEN = os.environ["TOKEN"]
    proxies = {
        "http": os.environ['QUOTAGUARDSTATIC_URL']
    }
    
client = commands.Bot(command_prefix='coc ', intents=intents)

# HELPERS:
def get_player_stats(tag):
    url = f'https://api.clashofclans.com/v1/players/{tag}'
    headers = {
        'Accept': '*/*',
        'authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    try:
        if 'http' in proxies:
            response = requests.get(url, headers=headers, proxies=proxies)
        else:
            response = requests.get(url, headers=headers)
        response.raise_for_status()
    except:
        return "There was an error with the request. Please try again later."
    
    res = response.json()
    print('res: ', res)
    return res

# BEGIN COC STATS HELPERS
def get_stats_embed(tag):
    data = get_player_stats(tag)
    print('data: ', data)
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

def write_json(author_id, tag):
    try:
        with open('data.json', "rt") as d:
            data = json.load(d)
    except:
        data = {}
        
    data[author_id] = {
        'player_tag': f'{tag}'
    }

    with open("data.json", "wt") as fp:
        json.dump(data, fp, indent=4)

# END COC VERIFY HELPERS
# BEGIN COC GRAPH HELPERS
def plot_trophy_graph(data, author_id):
    dates = list(data[author_id]['trophy_data'].keys())
    trophy_values = list(map(int, list(data[author_id]['trophy_data'].values())))
    
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
    
    with open("data.json", "wt") as fp:
        json.dump(data, fp, indent=4)
        
    plt.savefig('graph.png')
    plt.clf()

def set_graph_embed(author_name):
    embed_var = discord.Embed(
        title=f"**{author_name}** Trophy Graph",
        description="All-time Graph",
        color=0x000000
    )
    embed_var.set_image(url="attachment://image.png")
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
    with open('data.json', "rt") as d:
        data = json.load(d)
        if str(ctx.author.id) in data:
            await ctx.send(embed=get_stats_embed(data[str(ctx.author.id)]["player_tag"]))
            return
    if tag == "0":
        await ctx.send("Please enter a tag or run `coc verify` to use `coc stats` without entering a player tag. ")
        return
    tag = tag.replace('#', "%23")
    await ctx.send(embed=get_stats_embed(tag))

@client.command()
async def verify(ctx):
    with open('data.json', "rt") as d:
        data = json.load(d)
        if str(ctx.author.id) in data:
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
        if 'http' in proxies:
            response = requests.post(
                url,
                json=token_data,
                headers=headers,
                proxies=proxies
            )
            response.raise_for_status()
        else:
            response = requests.post(
                url,
                json=token_data,
                headers=headers,
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
            
            write_json(ctx.author.id, user_tag)
            
            embed_var = set_verify_embed(ctx.author.name)
            await ctx.send(embed=embed_var)
            await ctx.author.send("Verified!") # send verified in dm
        else:
            print(res)
            await ctx.author.send("Please try again by saying `coc verify` in the server. Check for typos.")
@client.command()
async def graph(ctx):
    with open('data.json', "rt") as d:
        data = json.load(d)
    if str(ctx.author.id) not in data:
        await ctx.send("Please verify by using `coc verify` to use `coc graph`")
        return
    
    author_id = str(ctx.author.id)
    if 'trophy_data' not in data[author_id]:
        data[author_id]['trophy_data'] = {}
        
    today = str(date.today().strftime('%b %d %y'))
    if today in data[author_id]['trophy_data']:
        await ctx.send('You have already graphed your trophies for today. Please come back tomorrow.')
        return
    
    tag = data[author_id]['player_tag']
    player_stats = get_player_stats(tag)
    current_trophy_count = str(player_stats['trophies'])
    data[author_id]['trophy_data'][today] = current_trophy_count
    
    plot_trophy_graph(data, author_id)
    
    file = discord.File("./graph.png", filename="image.png")
    await ctx.send(file=file, embed=set_graph_embed(ctx.author.name))
    

client.run(TOKEN)


