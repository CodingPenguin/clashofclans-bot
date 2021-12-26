from discord import Embed
async def fetch_general_clan_stats(clan_stats) -> Embed:
    clan_name = clan_stats['name']
    first_content_page = Embed(
        title=f"**{clan_name}** (Level {clan_stats['clan_level']})",
        color=0x000000
    )
    first_content_page.add_field(
        name='Description 📝',
        value=clan_stats['description'],
        inline=False
    )
    first_content_page.add_field(
        name='Member Count 🫂',
        value=f"{clan_stats['member_count']}/50",
        inline=True
    )
    first_content_page.add_field(
        name='Location 🌎',
        value=clan_stats['location']['name'],
        inline=True
    )
    
    if clan_stats['type'] == 'inviteOnly':
        availability = 'Invite Only'
    elif clan_stats['type'] == 'closed':
        availability = 'Closed'
    elif clan_stats['type'] == 'open':
        availability = 'Open'
    first_content_page.add_field(
        name='Availability ✉️',
        value=f'{availability}\n',
        inline=True
    )
    first_content_page.add_field(
        name='War Winstreak 💫',
        value=clan_stats['war_ws'],
        inline=True
    )
    first_content_page.add_field(
        name='Total War Wins ⚔️',
        value=clan_stats['war_wins'],
        inline=True
    )
    first_content_page.add_field(
        name='Clan War League 🎖',
        value=clan_stats['war_league']['name'],
        inline=True
    )
    
    return first_content_page