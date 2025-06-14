"""Command loader to import all command modules."""
import importlib


def load_all_commands():
    """Import all command modules to register their commands."""
    command_modules = [
        "commands.info_commands",
    ]

    for module_name in command_modules:
        importlib.import_module(module_name)
