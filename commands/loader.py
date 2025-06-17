"""Command loader to import all command modules."""
import importlib


def load_all_commands():
    """Import all command modules to register their commands."""
    command_modules = [
        "commands.debug_commands",
        "commands.help_commands",
        "commands.utility_commands",
        "commands.game_management_commands",
        "commands.player_management_commands",
        "commands.voting_commands",
        "commands.information_commands",
        "commands.communication_commands",
    ]

    for module_name in command_modules:
        importlib.import_module(module_name)
