"""Enhanced help commands that combine registry and hardcoded help."""
import logging
from typing import NamedTuple, Optional

import discord

import global_vars
from commands.command_enums import HelpSection, UserType
from commands.registry import registry, CommandInfo, CommandArgument
from model.settings.global_settings import GlobalSettings

# Type alias for user-defined aliases (alias_name -> command_name)
UserAliases = dict[str, str]

# Try to import config, create a mock config module if not available
try:
    import config
except ImportError:
    # Create a mock config module with default values for testing
    import types

    config = types.ModuleType('config')
    config.PREFIXES = (',', '@')

logging = logging.getLogger('discord')


# =============================================================================
# Data Structures
# =============================================================================

class HardcodedCommand(NamedTuple):
    name: str
    description: str
    aliases: tuple[str, ...] = ()


class CommandDisplay(NamedTuple):
    name: str
    description: str


class SectionInfo(NamedTuple):
    section_embed_title: str  # Title for individual section help page
    section_embed_description: str  # Description for individual section help page
    overview_field_name: str  # Field name in main storyteller help overview
    overview_field_description: str  # Field description in main storyteller help overview
    commands: tuple[HardcodedCommand, ...]  # Hardcoded commands for this section


# =============================================================================
# Help Generator Class
# =============================================================================

class HelpGenerator:
    """Generates help embeds from command registry."""

    # Shared dictionary for section information
    SECTION_INFO: dict[HelpSection, SectionInfo] = {
        HelpSection.COMMON: SectionInfo(
            section_embed_title="Common Commands",
            section_embed_description="Multiple arguments are space-separated.",
            overview_field_name="help common",
            overview_field_description="Prints commonly used storyteller commands.",
            commands=(
                HardcodedCommand("startgame", "starts the game"),
                HardcodedCommand("endgame <team>", "ends the game, with winner team"),
                HardcodedCommand("startday [players]", "starts the day, killing players"),
                HardcodedCommand("endday", "ends the day. if there is an execution, execute is preferred"),
                HardcodedCommand("kill <player>", "kills player"),
                HardcodedCommand("execute <player>", "executes player"),
                HardcodedCommand("exile <traveler>", "exiles traveler"),
                HardcodedCommand("setdeadline <time>",
                                 "sends a message with time in UTC as the deadline and opens nominations. The format can be HH:MM to specify a UTC time, or +HHhMMm to specify a relative time from now e.g. +3h15m; alternatively an epoch timestamp can be used - see https://www.epochconverter.com/"),
                HardcodedCommand("poison <player>", "poisons player"),
                HardcodedCommand("unpoison <player>", "unpoisons player"),
            )
        ),
        HelpSection.PROGRESSION: SectionInfo(
            section_embed_title="Game Progression",
            section_embed_description="Commands which progress game-time.",
            overview_field_name="help progression",
            overview_field_description="Prints commands which progress game-time.",
            commands=(
                HardcodedCommand("startgame", "starts the game"),
                HardcodedCommand("endgame <team>", "ends the game, with winner team"),
                HardcodedCommand("startday [players]", "starts the day, killing players"),
                HardcodedCommand("endday", "ends the day. if there is an execution, execute is preferred"),
            )
        ),
        HelpSection.DAY: SectionInfo(
            section_embed_title="Day-related",
            section_embed_description="Commands which affect variables related to the day.",
            overview_field_name="help day",
            overview_field_description="Prints commands related to the day.",
            commands=(
                HardcodedCommand("setdeadline <time>",
                                 "sends a message with time in UTC as the deadline and opens nominations. The format can be HH:MM to specify a UTC time, or +HHhMMm to specify a relative time from now e.g. +3h15m; alternatively an epoch timestamp can be used - see https://www.epochconverter.com/"),
                HardcodedCommand("openpms", "opens pms"),
                HardcodedCommand("opennoms", "opens nominations"),
                HardcodedCommand("open", "opens pms and nominations"),
                HardcodedCommand("closepms", "closes pms"),
                HardcodedCommand("closenoms", "closes nominations"),
                HardcodedCommand("close", "closes pms and nominations"),
                HardcodedCommand("vote", "votes for the current player"),
            )
        ),
        HelpSection.GAMESTATE: SectionInfo(
            section_embed_title="Game-State",
            section_embed_description="Commands which directly affect the game-state.",
            overview_field_name="help gamestate",
            overview_field_description="Prints commands which affect the game-state.",
            commands=(
                HardcodedCommand("kill <player>", "kills player"),
                HardcodedCommand("execute <player>", "executes player"),
                HardcodedCommand("exile <traveler>", "exiles traveler"),
                HardcodedCommand("revive <player>", "revives player"),
                HardcodedCommand("changerole <player>", "changes player's role"),
                HardcodedCommand("changealignment <player>", "changes player's alignment"),
                HardcodedCommand("changeability <player>",
                                 "changes player's ability, if applicable to their character (ex apprentice)"),
                HardcodedCommand("removeability <player>",
                                 "clears a player's modified ability, if applicable to their character (ex cannibal)"),
                HardcodedCommand("givedeadvote <player>", "adds a dead vote for player"),
                HardcodedCommand("removedeadvote <player>",
                                 "removes a dead vote from player. not necessary for ordinary usage"),
                HardcodedCommand("poison <player>", "poisons player"),
                HardcodedCommand("unpoison <player>", "unpoisons player"),
            )
        ),
        HelpSection.INFO: SectionInfo(
            section_embed_title="Informative",
            section_embed_description="Commands which display information about the game.",
            overview_field_name="help info",
            overview_field_description="Prints commands which display game information.",
            commands=(
                HardcodedCommand("history <player1> [player2]",
                                 "views the message history between player1 and player2, or all messages for player1"),
                HardcodedCommand("votehistory", "views all nominations and votes for those nominations"),
                HardcodedCommand("search <content>", "views all messages containing content"),
                HardcodedCommand("whispers <player>", "view a count of messages for the player per day"),
                HardcodedCommand("info <player>", "views game information about player"),
                HardcodedCommand("grimoire", "views the grimoire"),
            )
        ),
        HelpSection.CONFIGURE: SectionInfo(
            section_embed_title="Configuration",
            section_embed_description="Commands which configure how the bot works.",
            overview_field_name="help configure",
            overview_field_description="Prints commands which configures how the bot works.",
            commands=(
                HardcodedCommand("whispermode <all|neighbors|storytellers>", "sets whisper mode"),
                HardcodedCommand("enabletally", "enables display of whisper counts"),
                HardcodedCommand("disabletally", "disables display of whisper counts"),
                HardcodedCommand("setatheist <true|false>",
                                 "sets whether the atheist is on the script - this allows the storyteller to be nominated"),
                HardcodedCommand("automatekills <true|false>",
                                 "sets whether deaths are automated for certain characters (Riot, Golem, etc.).\nThis is not recommended for most games, as more work is needed from the Storytellers"),
            )
        ),
        HelpSection.MISC: SectionInfo(
            section_embed_title="Miscellaneous Commands",
            section_embed_description="Commands with miscellaneous uses, primarily for troubleshooting and seating.",
            overview_field_name="help misc",
            overview_field_description="Prints miscellaneous commands.",
            commands=(
                HardcodedCommand("notactive", "lists players who are yet to speak"),
                HardcodedCommand("makeinactive <player>",
                                 "marks player as inactive. must be done in all games player is participating in"),
                HardcodedCommand("undoinactive <player>",
                                 "undoes an inactivity mark. must be done in all games player is participating in"),
                HardcodedCommand("checkin <players>", "Marks players as checked in for tonight. Resets each day."),
                HardcodedCommand("undocheckin <players>", "Marks players as not checked in for tonight."),
                HardcodedCommand("addtraveler <player>", "adds player as a traveler", aliases=("addtraveller",)),
                HardcodedCommand("removetraveler <traveler>", "removes traveler from the game",
                                 aliases=("removetraveller",)),
                HardcodedCommand("cancelnomination", "cancels the previous nomination"),
                HardcodedCommand("reseat", "reseats the game"),
            )
        ),
        HelpSection.PLAYER: SectionInfo(
            section_embed_title="Player Commands",
            section_embed_description="Multiple arguments are space-separated.",
            overview_field_name="help player",
            overview_field_description="Prints the player help dialogue.",
            commands=(
                HardcodedCommand("pm <player>", "sends player a message", ("message",)),
                HardcodedCommand("history <player>", "views your message history with player"),
                HardcodedCommand("search <content>", "views all of your messages containing content"),
                HardcodedCommand("whispers", "view a count of your messages with other players per day"),
                HardcodedCommand("vote <yes|no>", "votes on an ongoing nomination"),
                HardcodedCommand("nominate <player>", "nominates player"),
                HardcodedCommand("presetvote <yes|no>",
                                 "submits a preset vote. will not work if it is your turn to vote. not recommended -- contact the storytellers instead",
                                 aliases=("prevote",)),
                HardcodedCommand("cancelprevote", "cancels an existing prevote"),
                HardcodedCommand("defaultvote [vote=no] [time=60]",
                                 "will always vote vote in time minutes. if no arguments given, deletes existing defaults."),
                HardcodedCommand("clear", "returns whitespace"),
                HardcodedCommand("cannominate", "lists players who are yet to nominate or skip"),
                HardcodedCommand("canbenominated", "lists players who are yet to be nominated"),
                HardcodedCommand("tocheckin", "lists players who are yet to check in"),
            )
        )
    }

    # Map of string names to help sections (automatically derived from SECTION_INFO)
    SECTION_MAP: dict[str, HelpSection] = {section.value: section for section in SECTION_INFO.keys()}

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    @staticmethod
    def _add_common_help_fields(embed: discord.Embed, user_type_text: str) -> None:
        """Add common help fields shared between storyteller and player embeds."""
        # Insert at beginning (index 0 and 1)
        embed.insert_field_at(
            index=0,
            name=f"New to {user_type_text} online?",
            value="Try the tutorial command! (not yet implemented)",
            inline=False,
        )
        embed.insert_field_at(
            index=1,
            name="Formatting commands",
            value="Use `{}` as a prefix (e.g., `{}ping`). Separate multiple arguments with spaces.".format(
                "` or `".join(config.PREFIXES),
                config.PREFIXES[0] if config.PREFIXES else ""),
            inline=False,
        )

        embed.add_field(
            name="Bot Questions?",
            value="Discuss or provide feedback at https://github.com/fiveofswords/botc-bot",
            inline=False,
        )

    @staticmethod
    def _combine_and_sort_commands(
            registry_commands: tuple[CommandInfo, ...],
            hardcoded_commands: tuple[HardcodedCommand, ...],
            user_type: UserType,
            user_aliases: Optional[UserAliases] = None
    ) -> list[CommandDisplay]:
        """Combine registry and hardcoded commands, deduplicate, and sort alphabetically.
        
        Args:
            registry_commands: Commands from the command registry
            hardcoded_commands: Hardcoded commands for the section
            user_type: User type for command formatting
            user_aliases: Optional user aliases (alias_name -> command_name)
        """

        # Convert user aliases to command -> [aliases] mapping
        user_aliases_by_command: dict[str, list[str]] = {}
        if user_aliases:
            for alias, command in user_aliases.items():
                if command not in user_aliases_by_command:
                    user_aliases_by_command[command] = []
                user_aliases_by_command[command].append(alias)

        seen = set()
        all_commands: list[CommandDisplay] = []

        # Registry commands
        for cmd in registry_commands:
            cmd_name = cmd.get_formatted_name_for_user(user_type)

            # Combine registry aliases + user aliases
            all_aliases = list(cmd.aliases) if getattr(cmd, 'aliases', None) else []
            if cmd.name in user_aliases_by_command:
                all_aliases.extend(user_aliases_by_command[cmd.name])

            if all_aliases:
                cmd_name += f" (aliases: {', '.join(all_aliases)})"
                
            if cmd.name not in seen:
                all_commands.append(CommandDisplay(cmd_name, cmd.get_description_for_user(user_type)))
                seen.add(cmd.name)

        # Hardcoded commands
        for cmd in hardcoded_commands:
            base_cmd = cmd.name.split()[0]
            if base_cmd not in seen:
                # Combine hardcoded aliases + user aliases
                all_aliases = list(cmd.aliases) if cmd.aliases else []
                if base_cmd in user_aliases_by_command:
                    all_aliases.extend(user_aliases_by_command[base_cmd])

                if all_aliases:
                    cmd_name = f"{cmd.name} (aliases: {', '.join(all_aliases)})"
                else:
                    cmd_name = cmd.name

                all_commands.append(CommandDisplay(cmd_name, cmd.description))
                seen.add(base_cmd)

        all_commands.sort(key=lambda x: x.name.lower())
        return all_commands

    # =========================================================================
    # Public Embed Creation Methods
    # =========================================================================

    @staticmethod
    def create_storyteller_help_embed() -> discord.Embed:
        """Create the main storyteller help embed."""
        embed = discord.Embed(
            title="Storyteller Help",
            description="Welcome to the storyteller help dialogue!",
        )

        # Add help sections dynamically from shared dictionary
        for section, info in HelpGenerator.SECTION_INFO.items():
            embed.add_field(
                name=info.overview_field_name,
                value=info.overview_field_description,
                inline=False,
            )

        HelpGenerator._add_common_help_fields(embed, "storytelling")
        return embed

    @staticmethod
    def create_section_help_embed(section: HelpSection,
                                  user_type: UserType,
                                  user_aliases: Optional[UserAliases] = None) -> discord.Embed:
        """Create a help embed for a specific section with integrated registry + hardcoded commands.
        
        Args:
            section: Help section to generate embed for
            user_type: User type for command formatting
            user_aliases: Optional user aliases (alias_name -> command_name)
        """
        section_info = HelpGenerator.SECTION_INFO[section]

        embed = discord.Embed(
            title=section_info.section_embed_title,
            description=section_info.section_embed_description,
        )

        # Add registry and hardcoded commands for the section
        hardcoded_commands: tuple[HardcodedCommand, ...] = section_info.commands
        registry_commands: tuple[CommandInfo, ...] = registry.get_commands_by_section(section)

        all_commands = HelpGenerator._combine_and_sort_commands(
            registry_commands, hardcoded_commands, user_type, user_aliases
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
    def create_player_help_embed(user_aliases: Optional[UserAliases] = None) -> discord.Embed:
        """Create help embed for player commands with integrated registry + hardcoded commands, sorted alphabetically.
        
        Args:
            user_aliases: Optional user aliases (alias_name -> command_name)
        """
        embed = HelpGenerator.create_section_help_embed(HelpSection.PLAYER, UserType.PLAYER, user_aliases)
        HelpGenerator._add_common_help_fields(embed, "playing")
        return embed


# =============================================================================
# Command Registration
# =============================================================================

# TODO: Create a separate Observer view showing help for observer commands
@registry.command(
    name="help",
    user_types=[UserType.STORYTELLER, UserType.PLAYER, UserType.OBSERVER, UserType.NONE],
    arguments={
        UserType.STORYTELLER: [
            CommandArgument(("common", "progression", "day", "gamestate", "configure", "info", "misc"), optional=True)
        ],
        UserType.OBSERVER: [],
        UserType.PLAYER: [],
        UserType.NONE: []
    },
    description="Display help information for bot commands",
    help_sections=[HelpSection.MISC, HelpSection.PLAYER]
)
async def help_command(message: discord.Message, argument: str):
    """Enhanced help command that combines registry commands with existing hardcoded help."""

    # Load user aliases
    user_aliases = None
    try:
        user_aliases = GlobalSettings.load().get_aliases(message.author.id)
    except Exception as e:
        # If there's any error loading user aliases, continue without them
        logging.warning(f"Failed to load user aliases for {message.author.id}: {e}")
        pass

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
            embed = HelpGenerator.create_player_help_embed(user_aliases)
        else:
            # Try to match a help section
            section = HelpGenerator.SECTION_MAP.get(argument)
            if section:
                embed = HelpGenerator.create_section_help_embed(section, UserType.STORYTELLER, user_aliases)
            else:
                # Unknown help topic
                await message.author.send(f"Unknown help topic: {argument}. Use `@help` to see available topics.")
                return
    else:
        # PLAYER HELP
        embed = HelpGenerator.create_player_help_embed(user_aliases)

    # Send the help embed as a DM
    # This is one of the rare places we use .send directly instead of safe_send
    # because we're sending embeds and safe_send isn't set up to split embeds if needed
    try:
        await message.author.send(embed=embed)
    except discord.Forbidden:
        logging.warning(f"Failed to send help DM to {message.author}. User has DMs disabled.")
