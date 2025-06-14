"""Enhanced help commands that combine registry and hardcoded help."""
import logging

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
        hardcoded_commands: list[tuple[str, str]] = HelpGenerator._get_hardcoded_commands_for_section(section)
        section_commands = []
        section_commands.extend(hardcoded_commands)
        for cmd in registry.get_commands_by_section(section, user_type):
            cmd_name = cmd.name
            if cmd.aliases:
                cmd_name += f" (aliases: {', '.join(cmd.aliases)})"
            section_commands.append((cmd_name, cmd.get_description_for_user(user_type)))
        section_commands.sort(key=lambda x: x[0].lower())  # Sort by command name

        for cmd_name, description in section_commands:
            embed.add_field(name=cmd_name, value=description, inline=False)

        if not section_commands:
            embed.add_field(
                name="No commands found",
                value="No commands are available for this section yet.",
                inline=False
            )

        return embed

    @staticmethod
    def _get_hardcoded_commands_for_section(section: commands.help_types.HelpSection) -> list[tuple[str, str]]:
        """Get hardcoded commands for a specific section."""
        hardcoded_map = {
            commands.help_types.HelpSection.COMMON: [
                ("startgame", "starts the game"),
                ("endgame <<team>>", "ends the game with winner team"),
                ("startday <<players>>", "starts the day, killing players"),
                ("endday", "ends the day"),
                ("kill <<player>>", "kills player"),
                ("execute <<player>>", "executes player"),
                ("exile <<traveler>>", "exiles traveler"),
                ("setdeadline <time>", "sets deadline and opens nominations"),
                ("poison <<player>>", "poisons player"),
                ("unpoison <<player>>", "unpoisons player"),
            ],
            commands.help_types.HelpSection.PROGRESSION: [
                ("startgame", "starts the game"),
                ("endgame <<team>>", "ends the game with winner team"),
                ("startday <<players>>", "starts the day, killing players"),
                ("endday", "ends the day"),
            ],
            commands.help_types.HelpSection.DAY: [
                ("setdeadline <time>", "sets deadline and opens nominations"),
                ("openpms", "opens private messages"),
                ("opennoms", "opens nominations"),
                ("open", "opens both PMs and nominations"),
                ("closepms", "closes private messages"),
                ("closenoms", "closes nominations"),
                ("close", "closes both PMs and nominations"),
                ("vote", "votes for the current player"),
            ],
            commands.help_types.HelpSection.GAMESTATE: [
                ("kill <<player>>", "kills player"),
                ("execute <<player>>", "executes player"),
                ("exile <<traveler>>", "exiles traveler"),
                ("revive <<player>>", "revives player"),
                ("changerole <<player>>", "changes player's role"),
                ("changealignment <<player>>", "changes player's alignment"),
                ("changeability <<player>>", "changes player's ability"),
                ("removeability <<player>>", "clears player's modified ability"),
                ("givedeadvote <<player>>", "adds a dead vote for player"),
                ("removedeadvote <<player>>", "removes a dead vote from player"),
                ("poison <<player>>", "poisons player"),
                ("unpoison <<player>>", "unpoisons player"),
            ],
            commands.help_types.HelpSection.CONFIGURE: [
                ("whispermode <<all/neighbors/storytellers>>", "sets whisper mode"),
                ("enabletally", "enables display of whisper counts"),
                ("disabletally", "disables display of whisper counts"),
                ("setatheist <<true/false>>", "sets whether atheist is on script"),
                ("automatekills <<true/false>>", "sets whether deaths are automated"),
            ],
            commands.help_types.HelpSection.INFO: [
                ("history <<player1>> <<player2>>", "views message history between players"),
                ("history <<player>>", "views all of player's messages"),
                ("votehistory", "views all nominations and votes"),
                ("search <<content>>", "views all messages containing content"),
                ("whispers <<player>>", "view message count for player per day"),
                ("info <<player>>", "views game information about player"),
                ("grimoire", "views the grimoire"),
            ],
            commands.help_types.HelpSection.MISC: [
                ("notactive", "lists players who are yet to speak"),
                ("makeinactive <<player>>", "marks player as inactive"),
                ("undoinactive <<player>>", "undoes an inactivity mark"),
                ("checkin <<players>>", "marks players as checked in"),
                ("undocheckin <<players>>", "marks players as not checked in"),
                ("addtraveler <<player>>", "adds player as a traveler"),
                ("removetraveler <<traveler>>", "removes traveler from game"),
                ("cancelnomination", "cancels the previous nomination"),
                ("reseat", "reseats the game"),
            ],
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

        # Remove duplicates
        seen = set()
        unique_commands = []
        for cmd in registry_commands:
            if cmd.name not in seen:
                seen.add(cmd.name)
                unique_commands.append(cmd)

        # Prepare all commands (registry + hardcoded) for sorting
        all_commands = []
        for cmd in unique_commands:
            cmd_name = cmd.name
            if cmd.aliases:
                cmd_name += f" (aliases: {', '.join(cmd.aliases)})"
            all_commands.append((cmd_name, cmd.get_description_for_user(commands.help_types.UserType.PLAYER)))

        # Add hardcoded player commands that aren't in registry
        hardcoded_commands = [
            ("pm <<player>>", "sends player a message", ["message"]),
            ("history <<player>>", "views message history with player", []),
            ("search <<content>>", "views messages containing content", []),
            ("whispers", "view message count with other players per day", []),
            ("vote <<yes/no>>", "votes on ongoing nomination", []),
            ("nominate <<player>>", "nominates player", []),
            ("presetvote <<yes/no>>", "submits preset vote", ["prevote"]),
            ("cancelprevote", "cancels existing prevote", []),
            ("defaultvote <<vote = 'no'>> <<time=60>>", "sets default vote behavior", []),
            ("makealias <<alias>> <<command>>", "creates command alias", []),
            ("clear", "returns whitespace", []),
            ("cannominate", "lists players who can still nominate", []),
            ("canbenominated", "lists players who can be nominated", []),
            ("tocheckin", "lists players who need to check in", []),
        ]

        for cmd_name, description, aliases in hardcoded_commands:
            base_cmd = cmd_name.split()[0]
            if base_cmd not in seen:
                if aliases:
                    cmd_name += f" (aliases: {', '.join(aliases)})"
                all_commands.append((cmd_name, description))
                seen.add(base_cmd)

        # Sort all commands alphabetically by command name
        all_commands.sort(key=lambda x: x[0].lower())

        for cmd_name, description in all_commands:
            embed.add_field(name=cmd_name, value=description, inline=False)

        # Add having issues section
        embed.add_field(
            name="Having issues?",
            value="Report it here: https://github.com/Kye-Evans/botc-bot/issues",
            inline=False,
        )

        return embed


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
