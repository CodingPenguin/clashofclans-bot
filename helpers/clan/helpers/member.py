from discord import Embed
import math
import numpy as np

async def fetch_member_stats(clan_stats) -> Embed:
    clan_name = clan_stats['name']
    member_page = Embed(
        title=f"**{clan_name}** Member Stats",
        color=0x000000
    )
    
    trophy_sum = 0
    donation_counts = []
    donation_received_counts = []
    max_donations = 0
    top_donator = ''
    clan_size = len(clan_stats['members'])
    for idx in range(clan_size):
        member = clan_stats['members'][idx]
        if member['donations'] > max_donations:
            max_donations = member['donations']
            top_donator = member['name']
        trophy_sum += member['trophies']
        donation_counts.append(member['donations'])
        donation_received_counts.append(member['donations_received'])
    
    median_donations = np.median(donation_counts)
    average_trophies = round(trophy_sum / clan_size, 2)
    
    member_page.add_field(
        name='Top Donator ⭐',
        value=f'{top_donator}, with {max_donations} donations',
        inline=True
    )
    member_page.add_field(
        name='Median Donations 🤲',
        value=median_donations,
        inline=True
    )    
    member_page.add_field(
        name='Average Trophies 🏆',
        value=average_trophies,
        inline=True
    )
    
    top_fifth = math.floor(clan_size / 5)
    member_page.add_field(
        name=f'Leaderboard (Top {top_fifth})',
        value='sorted by trophies',
        inline=False
    )
    for idx in range(top_fifth):
        member = clan_stats['members'][idx]
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
        member_page.add_field(
            name=f"{idx+1}. {member['name']} ({role})",
            value=f"{member['league']['name']}: {member['trophies']} 🏆\nVersus: {member['versus_trophies']} 🏆\nDonation Ratio: {donation_ratio} ({member['donations']}/{member['donations_received']}) 🤲",
            inline=False
        )
    return member_page