"""Enhanced help commands that combine registry and hardcoded help."""
import logging
from typing import NamedTuple, List

import discord

import commands.help_types
import global_vars
from commands.registry import registry

# Try to import config, create a mock config module if not available
try:
    import config
except ImportError:
    # Create a mock config module with default values for testing
    import types

    config = types.ModuleType('config')
    config.PREFIXES = (',', '@')

logging = logging.getLogger('discord')


class HardcodedCommand(NamedTuple):
    name: str
    description: str
    aliases: List[str]


class CommandDisplay(NamedTuple):
    name: str
    description: str


class HelpGenerator:
    """Generates help embeds from command registry."""

    @staticmethod
    def _add_common_help_fields(embed: discord.Embed, user_type_text: str) -> None:
        """Add common help fields shared between storyteller and player embeds."""
        embed.add_field(
            name=f"New to {user_type_text} online?",
            value="Try the tutorial command! (not yet implemented)",
            inline=False,
        )
        embed.add_field(
            name="Formatting commands",
            value="Use `{}` as a prefix (e.g., `{}ping`). Separate multiple arguments with spaces.".format(
                "` or `".join(config.PREFIXES),
                config.PREFIXES[0] if config.PREFIXES else ""),
        )

    @staticmethod
    def _add_issues_field(embed: discord.Embed) -> None:
        """Add the issues reporting field to an embed."""
        embed.add_field(
            name="Having issues?",
            value="Report it here: https://github.com/Kye-Evans/botc-bot/issues",
            inline=False,
        )

    # Shared dictionary for section information
    SECTION_INFO = {
        commands.help_types.HelpSection.COMMON: {
            "title": "Common Commands",
            "description": "Prints commonly used storyteller commands."
        },
        commands.help_types.HelpSection.PROGRESSION: {
            "title": "Game Progression Commands",
            "description": "Prints game progression commands."
        },
        commands.help_types.HelpSection.DAY: {
            "title": "Day-related Commands",
            "description": "Prints day-related commands."
        },
        commands.help_types.HelpSection.GAMESTATE: {
            "title": "Game State Commands",
            "description": "Prints game state modification commands."
        },
        commands.help_types.HelpSection.CONFIGURE: {
            "title": "Configuration Commands",
            "description": "Prints bot configuration commands."
        },
        commands.help_types.HelpSection.INFO: {
            "title": "Information Commands",
            "description": "Prints information display commands."
        },
        commands.help_types.HelpSection.MISC: {
            "title": "Miscellaneous Commands",
            "description": "Prints miscellaneous commands."
        },
        commands.help_types.HelpSection.PLAYER: {
            "title": "Player Commands",
            "description": "Prints player commands."
        }
    }

    @staticmethod
    def create_storyteller_help_embed() -> discord.Embed:
        """Create the main storyteller help embed."""
        embed = discord.Embed(
            title="Storyteller Help",
            description="Welcome to the storyteller help dialogue!",
        )
        HelpGenerator._add_common_help_fields(embed, "storytelling")

        # Add help sections dynamically from shared dictionary
        for section, info in HelpGenerator.SECTION_INFO.items():
            embed.add_field(
                name=f"help {section.value}",
                value=info["description"],
                inline=False,
            )

        HelpGenerator._add_issues_field(embed)
        return embed

    @staticmethod
    def create_section_help_embed(section: commands.help_types.HelpSection,
                                  user_type: commands.help_types.UserType) -> discord.Embed:
        """Create a help embed for a specific section with integrated registry + hardcoded commands."""
        section_info = HelpGenerator.SECTION_INFO.get(section)

        embed = discord.Embed(
            title=section_info["title"] if section_info else f"{section.value.title()} Commands",
            description=f"Commands in the {section.value} category",
        )

        # Add registry and hardcoded commands for the section
        hardcoded_commands: list[HardcodedCommand] = HelpGenerator._get_hardcoded_commands_for_section(section)
        registry_commands = registry.get_commands_by_section(section, user_type)
        
        all_commands = HelpGenerator._combine_and_sort_commands(
            registry_commands, hardcoded_commands, user_type
        )

        for cmd in all_commands:
            embed.add_field(name=cmd.name, value=cmd.description, inline=False)

        if not all_commands:
            embed.add_field(
                name="No commands found",
                value="No commands are available for this section yet.",
                inline=False
            )

        return embed

    @staticmethod
    def _get_hardcoded_commands_for_section(section: commands.help_types.HelpSection) -> list[HardcodedCommand]:
        """Get hardcoded commands for a specific section."""
        hardcoded_map = {
            commands.help_types.HelpSection.COMMON: [
                HardcodedCommand("startgame", "starts the game", []),
                HardcodedCommand("endgame <<team>>", "ends the game with winner team", []),
                HardcodedCommand("startday <<players>>", "starts the day, killing players", []),
                HardcodedCommand("endday", "ends the day", []),
                HardcodedCommand("kill <<player>>", "kills player", []),
                HardcodedCommand("execute <<player>>", "executes player", []),
                HardcodedCommand("exile <<traveler>>", "exiles traveler", []),
                HardcodedCommand("setdeadline <time>", "sets deadline and opens nominations", []),
                HardcodedCommand("poison <<player>>", "poisons player", []),
                HardcodedCommand("unpoison <<player>>", "unpoisons player", []),
            ],
            commands.help_types.HelpSection.PROGRESSION: [
                HardcodedCommand("startgame", "starts the game", []),
                HardcodedCommand("endgame <<team>>", "ends the game with winner team", []),
                HardcodedCommand("startday <<players>>", "starts the day, killing players", []),
                HardcodedCommand("endday", "ends the day", []),
            ],
            commands.help_types.HelpSection.DAY: [
                HardcodedCommand("setdeadline <time>", "sets deadline and opens nominations", []),
                HardcodedCommand("openpms", "opens private messages", []),
                HardcodedCommand("opennoms", "opens nominations", []),
                HardcodedCommand("open", "opens both PMs and nominations", []),
                HardcodedCommand("closepms", "closes private messages", []),
                HardcodedCommand("closenoms", "closes nominations", []),
                HardcodedCommand("close", "closes both PMs and nominations", []),
                HardcodedCommand("vote", "votes for the current player", []),
            ],
            commands.help_types.HelpSection.GAMESTATE: [
                HardcodedCommand("kill <<player>>", "kills player", []),
                HardcodedCommand("execute <<player>>", "executes player", []),
                HardcodedCommand("exile <<traveler>>", "exiles traveler", []),
                HardcodedCommand("revive <<player>>", "revives player", []),
                HardcodedCommand("changerole <<player>>", "changes player's role", []),
                HardcodedCommand("changealignment <<player>>", "changes player's alignment", []),
                HardcodedCommand("changeability <<player>>", "changes player's ability", []),
                HardcodedCommand("removeability <<player>>", "clears player's modified ability", []),
                HardcodedCommand("givedeadvote <<player>>", "adds a dead vote for player", []),
                HardcodedCommand("removedeadvote <<player>>", "removes a dead vote from player", []),
                HardcodedCommand("poison <<player>>", "poisons player", []),
                HardcodedCommand("unpoison <<player>>", "unpoisons player", []),
            ],
            commands.help_types.HelpSection.CONFIGURE: [
                HardcodedCommand("whispermode <<all/neighbors/storytellers>>", "sets whisper mode", []),
                HardcodedCommand("enabletally", "enables display of whisper counts", []),
                HardcodedCommand("disabletally", "disables display of whisper counts", []),
                HardcodedCommand("setatheist <<true/false>>", "sets whether atheist is on script", []),
                HardcodedCommand("automatekills <<true/false>>", "sets whether deaths are automated", []),
            ],
            commands.help_types.HelpSection.INFO: [
                HardcodedCommand("history <<player1>> <<player2>>", "views message history between players", []),
                HardcodedCommand("history <<player>>", "views all of player's messages", []),
                HardcodedCommand("votehistory", "views all nominations and votes", []),
                HardcodedCommand("search <<content>>", "views all messages containing content", []),
                HardcodedCommand("whispers <<player>>", "view message count for player per day", []),
                HardcodedCommand("info <<player>>", "views game information about player", []),
                HardcodedCommand("grimoire", "views the grimoire", []),
            ],
            commands.help_types.HelpSection.MISC: [
                HardcodedCommand("notactive", "lists players who are yet to speak", []),
                HardcodedCommand("makeinactive <<player>>", "marks player as inactive", []),
                HardcodedCommand("undoinactive <<player>>", "undoes an inactivity mark", []),
                HardcodedCommand("checkin <<players>>", "marks players as checked in", []),
                HardcodedCommand("undocheckin <<players>>", "marks players as not checked in", []),
                HardcodedCommand("addtraveler <<player>>", "adds player as a traveler", []),
                HardcodedCommand("removetraveler <<traveler>>", "removes traveler from game", []),
                HardcodedCommand("cancelnomination", "cancels the previous nomination", []),
                HardcodedCommand("reseat", "reseats the game", []),
            ],
            # This section is for commands available to players
            commands.help_types.HelpSection.PLAYER: [
                HardcodedCommand("pm <<player>>", "sends player a message", ["message"]),
                HardcodedCommand("history <<player>>", "views message history with player", []),
                HardcodedCommand("search <<content>>", "views messages containing content", []),
                HardcodedCommand("whispers", "view message count with other players per day", []),
                HardcodedCommand("vote <<yes/no>>", "votes on ongoing nomination", []),
                HardcodedCommand("nominate <<player>>", "nominates player", []),
                HardcodedCommand("presetvote <<yes/no>>", "submits preset vote", ["prevote"]),
                HardcodedCommand("cancelprevote", "cancels existing prevote", []),
                HardcodedCommand("defaultvote <<vote = 'no'>> <<time=60>>", "sets default vote behavior", []),
                HardcodedCommand("makealias <<alias>> <<command>>", "creates command alias", []),
                HardcodedCommand("clear", "returns whitespace", []),
                HardcodedCommand("cannominate", "lists players who can still nominate", []),
                HardcodedCommand("canbenominated", "lists players who can be nominated", []),
                HardcodedCommand("tocheckin", "lists players who need to check in", []),
            ]
        }
        return hardcoded_map.get(section, [])

    @staticmethod
    def create_player_help_embed() -> discord.Embed:
        """Create help embed for player commands with integrated registry + hardcoded commands, sorted alphabetically."""
        embed = discord.Embed(
            title="Player Commands",
            description="Commands available to all players",
        )

        # Add common help fields
        HelpGenerator._add_common_help_fields(embed, "playing")

        # Add registry commands for players
        registry_commands = registry.get_commands_by_user_type(commands.help_types.UserType.PLAYER)
        registry_commands.extend(
            registry.get_commands_by_section(commands.help_types.HelpSection.PLAYER, commands.help_types.UserType.ALL))

        # Add hardcoded player commands that aren't in registry
        hardcoded_commands = HelpGenerator._get_hardcoded_commands_for_section(commands.help_types.HelpSection.PLAYER)
        all_commands = HelpGenerator._combine_and_sort_commands(
            registry_commands, hardcoded_commands, commands.help_types.UserType.PLAYER
        )
        for cmd in all_commands:
            embed.add_field(name=cmd.name, value=cmd.description, inline=False)

        # Add having issues section
        embed.add_field(
            name="Having issues?",
            value="Report it here: https://github.com/Kye-Evans/botc-bot/issues",
            inline=False,
        )

        return embed

    @staticmethod
    def _combine_and_sort_commands(
            registry_commands: list,
            hardcoded_commands: list[HardcodedCommand],
            user_type: commands.help_types.UserType
    ) -> list['CommandDisplay']:
        """Combine registry and hardcoded commands, deduplicate, and sort alphabetically."""

        seen = set()
        all_commands: list[CommandDisplay] = []
        # Registry commands
        for cmd in registry_commands:
            cmd_name = cmd.name
            if getattr(cmd, 'aliases', None):
                cmd_name += f" (aliases: {', '.join(cmd.aliases)})"
            if cmd.name not in seen:
                all_commands.append(CommandDisplay(cmd_name, cmd.get_description_for_user(user_type)))
                seen.add(cmd.name)
        # Hardcoded commands
        for cmd in hardcoded_commands:
            base_cmd = cmd.name.split()[0]
            if base_cmd not in seen:
                if cmd.aliases:
                    cmd_name = f"{cmd.name} (aliases: {', '.join(cmd.aliases)})"
                else:
                    cmd_name = cmd.name
                all_commands.append(CommandDisplay(cmd_name, cmd.description))
                seen.add(base_cmd)
        all_commands.sort(key=lambda x: x.name.lower())
        return all_commands


@registry.command(
    name="help",
    description="Display help information for bot commands",
    help_sections=[commands.help_types.HelpSection.INFO],
    user_types=[commands.help_types.UserType.ALL]
)
async def help_command(message: discord.Message, argument: str):
    """Enhanced help command that combines registry commands with existing hardcoded help."""

    # Determine user type
    is_storyteller = global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles

    # Parse help argument
    argument = argument.strip().lower()

    if is_storyteller:
        # STORYTELLER HELP
        if argument == "":
            # Main storyteller help menu
            embed = HelpGenerator.create_storyteller_help_embed()
        elif argument == "player":
            # Show player commands
            embed = HelpGenerator.create_player_help_embed()
        else:
            # Try to match a help section
            section_map = {
                "common": commands.help_types.HelpSection.COMMON,
                "progression": commands.help_types.HelpSection.PROGRESSION,
                "day": commands.help_types.HelpSection.DAY,
                "gamestate": commands.help_types.HelpSection.GAMESTATE,
                "configure": commands.help_types.HelpSection.CONFIGURE,
                "info": commands.help_types.HelpSection.INFO,
                "misc": commands.help_types.HelpSection.MISC
            }

            section = section_map.get(argument)
            if section:
                embed = HelpGenerator.create_section_help_embed(section, commands.help_types.UserType.STORYTELLER)
            else:
                # Unknown help topic
                await message.author.send(f"Unknown help topic: {argument}. Use `@help` to see available topics.")
                return
    else:
        # PLAYER HELP
        embed = HelpGenerator.create_player_help_embed()

    # Send the help embed as a DM
    # This is one of the rare places we use .send directly instead of safe_send
    # because we're sending embeds and safe_send isn't set up to split embeds if needed
    try:
        await message.author.send(embed=embed)
    except discord.Forbidden:
        logging.warning(f"Failed to send help DM to {message.author}. User has DMs disabled.")
