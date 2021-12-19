import discord
from env import MONGO_SRV_URL
from pymongo import MongoClient

mongo_client = MongoClient(MONGO_SRV_URL)
db = mongo_client.coc
col = db.users

def set_verify_embed(author_name: str) -> discord.Embed:
    embed_var = discord.Embed(
        title="Success! ✅",
        description=f"**{author_name}** has been verified!",
        color=0x32C12C
    )
    return embed_var


def write_to_db(author_id: str, tag: str) -> None:
    new_user_data = {
        "_id": author_id,
        'player_tag': tag,
        'trophy_data': {}
    }
    col.insert_one(new_user_data)
    
    