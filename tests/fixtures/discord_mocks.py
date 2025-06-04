"""
Mock Discord objects for testing the Blood on the Clocktower Discord bot.

This module provides mock implementations of Discord objects such as Member, Channel,
Message, Guild, and Role. These mocks simulate Discord API functionality without
using actual Discord servers or API calls.
"""

import datetime
from unittest.mock import MagicMock, AsyncMock

import discord
import pytest_asyncio

import global_vars


class MockClient:
    """Mock Discord client for testing."""

    def __init__(self):
        self.ws = MagicMock()
        self.ws.change_presence = AsyncMock()
        self.change_presence = AsyncMock()
        self.wait_for = AsyncMock()
        self.user = MagicMock()
        self.user.id = 999
        self.user.name = "Test Bot"


class MockRole:
    """Mock Discord role for testing."""

    def __init__(self, role_id, name):
        self.id = role_id
        self.name = name
        self.mention = f"<@&{role_id}>"
        self.members = []


class MockChannel:
    """Mock Discord channel for testing."""

    def __init__(self, channel_id, name):
        self.id = channel_id
        self.name = name
        self.messages = []

    async def send(self, content=None, embed=None):
        """Mock sending a message to the channel."""
        message = MockMessage(
            id=len(self.messages) + 1000,
            content=content,
            embed=embed,
            channel=self,
            author=MockMember(999, "Bot", "Blood on the Clocktower Bot")
        )
        self.messages.append(message)
        return message

    async def fetch_message(self, message_id):
        """Mock fetching a message by ID."""
        for message in self.messages:
            if message.id == message_id:
                return message
        raise discord.errors.NotFound(MagicMock(), "Message not found")

    async def pins(self):
        """Mock fetching pinned messages."""
        return [msg for msg in self.messages if msg.pinned]


class MockMember:
    """Mock Discord member for testing."""

    def __init__(self, member_id, name, display_name=None, roles=None, guild=None):
        self.id = member_id
        self.name = name
        self.display_name = display_name or name
        self.roles = roles or []
        self.mention = f"<@{member_id}>"
        self.dm_channel = MockChannel(member_id + 1000, f"dm-{name.lower()}")
        self.guild = guild

    async def add_roles(self, *roles):
        """Mock adding roles to member."""
        for role in roles:
            if role not in self.roles:
                self.roles.append(role)

    async def remove_roles(self, *roles):
        """Mock removing roles from member."""
        for role in roles:
            if role in self.roles:
                self.roles.remove(role)

    async def send(self, content=None, embed=None):
        """Mock sending a direct message to the user."""
        message = MockMessage(
            id=len(self.dm_channel.messages) + 2000,
            content=content,
            embed=embed,
            channel=self.dm_channel,
            author=MockMember(999, "Bot", "Blood on the Clocktower Bot")
        )
        self.dm_channel.messages.append(message)
        return message


class MockMessage:
    """Mock Discord message for testing."""

    def __init__(self, id, content=None, embed=None, channel=None, author=None, guild=None):
        self.id = id
        self.content = content
        self.embed = embed
        self.channel = channel
        self.author = author
        self.pinned = False
        self.created_at = datetime.datetime.now()
        self.jump_url = f"https://discord.com/channels/123/{channel.id if channel else 0}/{id}"
        # For direct messages, guild will be None
        self.guild = guild

    async def pin(self):
        """Mock pinning a message."""
        self.pinned = True

    async def unpin(self):
        """Mock unpinning a message."""
        self.pinned = False

    async def edit(self, content=None, embed=None):
        """Mock editing a message."""
        if content is not None:
            self.content = content
        if embed is not None:
            self.embed = embed


class MockGuild:
    """Mock Discord guild (server) for testing."""

    def __init__(self, id, name, members=None, roles=None, channels=None):
        self.id = id
        self.name = name
        self.members = members or []
        self.roles = roles or []
        self.channels = channels or []

    def get_member(self, member_id):
        """Get a member by ID."""
        for member in self.members:
            if member.id == member_id:
                return member
        return None

    def get_channel(self, channel_id):
        """Get a channel by ID."""
        for channel in self.channels:
            if channel.id == channel_id:
                return channel
        return None


@pytest_asyncio.fixture
async def mock_discord_setup():
    """Set up mock Discord environment for testing."""
    # Create a mock client and patch the real client
    mock_client = MockClient()

    # Create roles
    player_role = MockRole(100, "Player")
    traveler_role = MockRole(101, "Traveler")
    ghost_role = MockRole(102, "Ghost")
    dead_vote_role = MockRole(103, "Dead Vote")
    gamemaster_role = MockRole(104, "Storyteller")
    inactive_role = MockRole(105, "Inactive")
    observer_role = MockRole(106, "Observer")

    # Create channels
    town_square_channel = MockChannel(200, "town-square")
    game_category = MockChannel(201, "game-category")
    hands_channel = MockChannel(202, "hands")
    observer_channel = MockChannel(203, "observer")
    info_channel = MockChannel(204, "info")
    whisper_channel = MockChannel(205, "whispers")
    out_of_play_category = MockChannel(206, "out-of-play")
    st_channel1 = MockChannel(301, "st-alice")
    st_channel2 = MockChannel(302, "st-bob")
    st_channel3 = MockChannel(303, "st-charlie")

    # Create guild first
    guild = MockGuild(
        id=1000,
        name="Test Server",
        members=[],
        roles=[],
        channels=[]
    )

    # Create members with guild reference
    storyteller = MockMember(1, "Storyteller", roles=[gamemaster_role], guild=guild)
    alice = MockMember(2, "Alice", roles=[player_role], guild=guild)
    bob = MockMember(3, "Bob", roles=[player_role], guild=guild)
    charlie = MockMember(4, "Charlie", roles=[player_role], guild=guild)

    # Now update the guild with members, roles, and channels
    guild.members = [storyteller, alice, bob, charlie]
    guild.roles = [player_role, traveler_role, ghost_role, dead_vote_role, gamemaster_role, inactive_role,
                   observer_role]
    guild.channels = [town_square_channel, game_category, hands_channel, observer_channel, info_channel,
                      whisper_channel,
                      out_of_play_category, st_channel1, st_channel2, st_channel3]

    # Add storyteller to the gamemaster role members list
    gamemaster_role.members = [storyteller]

    # Set up global variables
    global_vars.server = guild
    global_vars.player_role = player_role
    global_vars.traveler_role = traveler_role
    global_vars.ghost_role = ghost_role
    global_vars.dead_vote_role = dead_vote_role
    global_vars.gamemaster_role = gamemaster_role
    global_vars.inactive_role = inactive_role
    global_vars.observer_role = observer_role
    global_vars.game_category = game_category
    global_vars.hands_channel = hands_channel
    global_vars.observer_channel = observer_channel
    global_vars.info_channel = info_channel
    global_vars.whisper_channel = whisper_channel
    global_vars.channel = town_square_channel
    global_vars.out_of_play_category = out_of_play_category

    # Return objects for tests to use
    return {
        'guild': guild,
        'client': mock_client,
        'roles': {
            'player': player_role,
            'traveler': traveler_role,
            'ghost': ghost_role,
            'dead_vote': dead_vote_role,
            'gamemaster': gamemaster_role,
            'inactive': inactive_role,
            'observer': observer_role
        },
        'channels': {
            'town_square': town_square_channel,
            'game_category': game_category,
            'hands': hands_channel,
            'observer': observer_channel,
            'info': info_channel,
            'whisper': whisper_channel,
            'out_of_play': out_of_play_category,
            'st1': st_channel1,
            'st2': st_channel2,
            'st3': st_channel3
        },
        'members': {
            'storyteller': storyteller,
            'alice': alice,
            'bob': bob,
            'charlie': charlie
        }
    }


def create_mock_message(id, content, channel, author, guild=None, embed=None):
    """Factory function to create a mock message."""
    return MockMessage(
        id=id,
        content=content,
        channel=channel,
        author=author,
        guild=guild,
        embed=embed
    )


def create_mock_channel(channel_id, name):
    """Factory function to create a mock channel."""
    return MockChannel(channel_id, name)


def create_mock_member(member_id, name, display_name=None, roles=None):
    """Factory function to create a mock member."""
    return MockMember(member_id, name, display_name, roles)
