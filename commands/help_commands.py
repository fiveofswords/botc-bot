"""Enhanced help commands that use the registry system."""
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

class CommandDisplay(NamedTuple):
    name: str
    description: str


class SectionInfo(NamedTuple):
    section_embed_title: str  # Title for individual section help page
    section_embed_description: str  # Description for individual section help page
    overview_field_name: str  # Field name in main storyteller help overview
    overview_field_description: str  # Field description in main storyteller help overview


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
            overview_field_description="Prints commonly used storyteller commands."
        ),
        HelpSection.PROGRESSION: SectionInfo(
            section_embed_title="Game Progression",
            section_embed_description="Commands which progress game-time.",
            overview_field_name="help progression",
            overview_field_description="Prints commands which progress game-time."
        ),
        HelpSection.DAY: SectionInfo(
            section_embed_title="Day-related",
            section_embed_description="Commands which affect variables related to the day.",
            overview_field_name="help day",
            overview_field_description="Prints commands related to the day."
        ),
        HelpSection.GAMESTATE: SectionInfo(
            section_embed_title="Game-State",
            section_embed_description="Commands which directly affect the game-state.",
            overview_field_name="help gamestate",
            overview_field_description="Prints commands which affect the game-state."
        ),
        HelpSection.INFO: SectionInfo(
            section_embed_title="Informative",
            section_embed_description="Commands which display information about the game.",
            overview_field_name="help info",
            overview_field_description="Prints commands which display game information."
        ),
        HelpSection.CONFIGURE: SectionInfo(
            section_embed_title="Configuration",
            section_embed_description="Commands which configure how the bot works.",
            overview_field_name="help configure",
            overview_field_description="Prints commands which configures how the bot works."
        ),
        HelpSection.MISC: SectionInfo(
            section_embed_title="Miscellaneous Commands",
            section_embed_description="Commands with miscellaneous uses, primarily for troubleshooting and seating.",
            overview_field_name="help misc",
            overview_field_description="Prints miscellaneous commands."
        ),
        HelpSection.PLAYER: SectionInfo(
            section_embed_title="Player Commands",
            section_embed_description="Multiple arguments are space-separated.",
            overview_field_name="help player",
            overview_field_description="Prints the player help dialogue."
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
    def _get_and_sort_commands(
            registry_commands: tuple[CommandInfo, ...],
            user_type: UserType,
            user_aliases: Optional[UserAliases] = None
    ) -> list[CommandDisplay]:
        """Get registry commands, format them, and sort alphabetically.
        
        Args:
            registry_commands: Commands from the command registry
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

            all_commands.append(CommandDisplay(cmd_name, cmd.get_description_for_user(user_type)))

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
        """Create a help embed for a specific section with registry commands.
        
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

        # Add registry commands for the section
        registry_commands: tuple[CommandInfo, ...] = registry.get_commands_by_section(section)

        all_commands = HelpGenerator._get_and_sort_commands(
            registry_commands, user_type, user_aliases
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
        """Create help embed for player commands with registry commands, sorted alphabetically.
        
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
    user_types=[UserType.STORYTELLER, UserType.PLAYER, UserType.OBSERVER, UserType.PUBLIC],
    arguments={
        UserType.STORYTELLER: [
            CommandArgument(("common", "progression", "day", "gamestate", "configure", "info", "misc"), optional=True)
        ],
        UserType.OBSERVER: [],
        UserType.PLAYER: [],
        UserType.PUBLIC: []
    },
    description="Display help information for bot commands",
    help_sections=[HelpSection.MISC, HelpSection.PLAYER]
)
async def help_command(message: discord.Message, argument: str):
    """Enhanced help command that uses the registry system."""

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
