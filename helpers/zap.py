import discord, math
from helpers.constants import AIRDEF_HPS, ZAP_APS

async def set_zap_embed(airdef, zap):
    print(AIRDEF_HPS)
    airdef_hp = AIRDEF_HPS[airdef]
    zap_ap = ZAP_APS[zap]
    amount_of_zaps = math.ceil(airdef_hp/zap_ap)
    embed_var = discord.Embed(
        title=f"How to destroy a level {airdef} Air Defense with level {zap} Lightning Spells:",
        description=f"⚡ Use {amount_of_zaps} of your level {zap} Lightning Spells ⚡",
        color=0x00A5F9
    )
    return embed_var