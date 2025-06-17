import discord

from commands.command_enums import HelpSection, UserType
from commands.registry import registry, CommandArgument
from model.settings import GlobalSettings
from utils import message_utils


@registry.command(
    name="makealias",
    description="Creates, removes, or lists aliases for commands (per-user).",
    help_sections=[HelpSection.MISC, HelpSection.PLAYER],
    user_types=[UserType.STORYTELLER, UserType.PLAYER, UserType.OBSERVER, UserType.PUBLIC],
    arguments=[CommandArgument("alias", optional=True), CommandArgument("command", optional=True)]
)
async def makealias_command(message: discord.Message, argument: str):
    """
    Creates, removes, or lists aliases for commands (per-user).
    Usage:
        - No arguments: List all aliases for the user.
        - One argument: Remove the alias for that user if it exists.
        - Two arguments: Create a per-user alias.
    """
    args = argument.split() if argument.strip() else []
    global_settings: GlobalSettings = GlobalSettings.load()
    user_id = message.author.id

    # If no arguments are provided, list all aliases for the user.
    if not args:
        aliases = global_settings.get_aliases(user_id)
        if aliases:
            alias_list = "\n".join([f"**{alias}** → {command}" for alias, command in sorted(aliases.items())])
            await message_utils.safe_send(message.author, f"Your aliases:\n{alias_list}")
        else:
            await message_utils.safe_send(message.author, "You have no aliases set.")
        return

    # If one argument is provided, remove the alias if it exists.
    if len(args) == 1:
        alias_term = args[0]
        if global_settings.get_alias(user_id, alias_term):
            global_settings.clear_alias(user_id, alias_term)
            global_settings.save()
            await message_utils.safe_send(message.author, f"Successfully removed alias {alias_term}.")
        else:
            await message_utils.safe_send(message.author, f"No alias named {alias_term} exists.")
        return

    # If two arguments are provided, create a new alias.
    if len(args) == 2:
        alias_term, command_term = args
        if alias_term in registry.get_all_commands():
            await message_utils.safe_send(
                message.author,
                f"Cannot alias the command '{alias_term}' as it is a registered command."
            )
            return
        global_settings.set_alias(user_id, alias_term, command_term)
        global_settings.save()
        await message_utils.safe_send(
            message.author,
            f"Successfully created alias {alias_term} for command {command_term}."
        )
        return

    # If there are too many arguments, send an error message.
    await message_utils.safe_send(
        message.author,
        f"makealias takes at most two arguments. You provided {len(args)}: {args}"
    )
