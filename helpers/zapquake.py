import discord, math
from helpers.constants import AIRDEF_HPS, QUAKE_APS, ZAP_APS

async def set_zapquake_embed(airdef: str, zap: str, quake: str) -> discord.Embed:
    airdef_hp = AIRDEF_HPS[airdef]
    zap_ap = ZAP_APS[zap]
    quake_ap = QUAKE_APS[quake]
    airdef_hp *= (1-quake_ap)
    amount_of_zaps = math.ceil(airdef_hp/zap_ap)
    
    embed_var = discord.Embed(
        title=f"How to destroy a level {airdef} Air Defense with level {zap} Lightning Spells and level {quake} Earthquake spells:",
        description=f"💨 Use 1 of your level {quake} Earthquake Spells FIRST! 💨\n⚡ Then use {amount_of_zaps} of your level {zap} Lightning Spells ⚡",
        color=0x00A5F9
    )
    return embed_var