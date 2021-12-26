from pydantic import BaseModel, Field
from typing import List


class WarLeagueBase(BaseModel):
    id: int = Field(...)
    name: str = Field(...)
    
class LocationBase(BaseModel):
    id: int = Field(...)
    name: str = Field(...)
    is_country: bool = Field(..., alias='isCountry')
    country_code: str = Field(..., alias='countryCode')
    
class BadgeBase(BaseModel):
    small: str = None
    medium: str = None
    large: str = None
    
class LeagueBase(BaseModel):
    id: int = Field(...)
    name: str = Field(...)
    icon_urls: BadgeBase = Field(..., alias='iconUrls')
    
class MemberBase(BaseModel):
    tag: str = Field(...)
    name: str = Field(...)
    role: str = Field(...)
    exp_level: int = Field(..., alias='expLevel')
    league: LeagueBase = Field(...)
    trophies: int = Field(...),
    versus_trophies: int = Field(..., alias='versusTrophies')
    clan_rank: int = Field(..., alias='previousClanRank')
    donations: int = Field(...)
    donations_received: int = Field(..., alias='donationsReceived')
    
class ClanBase(BaseModel):
    tag: str = Field(...)
    name: str = Field(...)
    type: str = Field(...)
    description: str = Field(...)
    location: LocationBase = Field(...)
    badge_urls: BadgeBase = Field(..., alias='badgeUrls')
    clan_level: int = Field(..., alias='clanLevel')
    clan_points: int = Field(..., alias='clanPoints')
    clan_versus_points: int = Field(..., alias='clanVersusPoints')
    required_trophies: int = Field(..., alias='requiredTrophies')
    war_ws: int = Field(..., alias='warWinStreak')
    war_wins: int = Field(..., alias='warWins')
    public_war_log: bool = Field(..., alias='isWarLogPublic')
    war_league: WarLeagueBase = Field(..., alias='warLeague')
    member_count: int = Field(..., alias='members')
    members: List[MemberBase] = Field(..., alias='memberList')
