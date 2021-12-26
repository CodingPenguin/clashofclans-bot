import asyncio
from discord import Embed
from loguru import logger


async def create_leaderboard_embed(clan_stats, starting_rank: int=0) -> Embed:

    leaderboard_page = Embed(
        title='Leaderboard',
        description='sorted by trophies'
    )
    for idx in range(len(clan_stats)):
        member = clan_stats[idx]
        if (role := member['role']) == 'leader':
            role = 'Leader'
        elif role == 'coLeader':
            role = 'Co-leader'
        elif role == 'admin':
            role = 'Elder'
        else:
            role = 'Member'
        
        if member['donations_received'] == 0:
            donation_ratio = member['donations']
        else:
            donation_ratio = round(member['donations'] / member['donations_received'], 3)
        leaderboard_page.add_field(
            name=f"{idx+starting_rank+1}. {member['name']} ({role})",
            value=f"{member['league']['name']}: {member['trophies']} 🏆\nVersus: {member['versus_trophies']} 🏆\nDonation Ratio: {donation_ratio} ({member['donations']}/{member['donations_received']}) 🤲",
            inline=False
        )
    return leaderboard_page

async def fetch_leaderboard(clan_stats) -> list[Embed]:
    embed_list = []
    new_embeds = []
    clan_size = clan_stats['member_count']
    
    if clan_size > 10 and clan_size <= 20:
        embed_list.append(clan_stats['members'][0:10])
        embed_list.append(clan_stats['members'][10:clan_size])
    if clan_size > 20 and clan_size <= 30:
        embed_list.append(clan_stats['members'][0:10])
        embed_list.append(clan_stats['members'][10:20])
        embed_list.append(clan_stats['members'][20:clan_size])
    if clan_size > 30 and clan_size <= 40:
        embed_list.append(clan_stats['members'][0:10])
        embed_list.append(clan_stats['members'][10:20])
        embed_list.append(clan_stats['members'][20:30])
        embed_list.append(clan_stats['members'][30:clan_size])
    if clan_size > 40 and clan_size <= 50:
        embed_list.append(clan_stats['members'][0:10])
        embed_list.append(clan_stats['members'][10:20])
        embed_list.append(clan_stats['members'][20:30])
        embed_list.append(clan_stats['members'][30:40])
        embed_list.append(clan_stats['members'][40:clan_size])
        
    for idx, embed in enumerate(embed_list):
        if idx == 0:
            new_embeds.append(create_leaderboard_embed(embed))
        elif idx == 1:
            new_embeds.append(create_leaderboard_embed(embed, 10))
        elif idx == 2:
            new_embeds.append(create_leaderboard_embed(embed, 20))
        elif idx == 3:
            new_embeds.append(create_leaderboard_embed(embed, 30))
        elif idx == 4:
            new_embeds.append(create_leaderboard_embed(embed, 40))
    
    new_embeds = await asyncio.gather(*new_embeds)
    return new_embeds