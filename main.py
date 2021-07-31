
import discord, requests, json, os

from discord.ext.commands.core import check
from discord.errors import HTTPException
from discord.ext import commands
from dotenv import load_dotenv
from requests import request

load_dotenv()

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix='coc ', intents=intents)
API_KEY = os.getenv("API_KEY")

#clan_tag = "#2PGJUGPR"

# HELPERS:

# BEGIN COC STATS HELPERS
def get_player_stats(tag):
    
    url = f'https://api.clashofclans.com/v1/players/{tag}'
    headers = {
        'Accept': '*/*',
        'authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except HTTPException as e:
        return "There was an error with the request. Please try again later."
    
    data = response.json()
    return(set_stats_embed(data["name"], data["trophies"], data["clan"]["name"]))
        

def set_stats_embed(name, trophies, clan):
    embed_var = discord.Embed(title=f"{name}'s Stats", color=0xD40C00)
    embed_var.add_field(name="Trophies 🏆", value=f"{trophies}", inline=False)
    embed_var.add_field(name="Clan ⚔️", value=f"{clan}", inline=False)
    
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
    except IOError:
        data = {}
        
    data[author_id] = f'{tag}'

    with open("data.json", "wt") as fp:
        json.dump(data, fp)

# END COC VERIFY HELPERS
    
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
        await ctx.send(embed=get_player_stats(data[str(ctx.author.id)]))
    elif tag == 0:
        await ctx.send("Please enter a tag")
    else:
        tag = tag.replace('#', "%23")
        await ctx.send(embed=get_player_stats(tag))

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
        response = requests.post(
            url,
            json=token_data,
            headers=headers
        )
        response.raise_for_status()
    except HTTPException as e:
        print('error: ', e)
        
        
    data = response.json()
    if 'status' in data:
        if data['status'] == 'ok':
            guild = client.get_guild(ctx.guild.id) # Get Guild w/ Guild ID
            role = discord.utils.get(guild.roles, name="verified player") # Get Role w/ Role ID
            member = guild.get_member(ctx.author.id) # Get member by author Id
            await member.add_roles(role)
            
            write_json(ctx.author.id, user_tag)
            
            embed_var = set_verify_embed(ctx.author.name)
            await ctx.send(embed=embed_var)
            await ctx.author.send("Verified!") # send verified in dm
        else:
            await ctx.author.send("Please try again by saying `coc verify` Check for typos.")
        
    

client.run(os.getenv('TOKEN'))


