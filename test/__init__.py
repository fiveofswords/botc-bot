from pathlib import Path
from importlib import import_module

# iterate through the modules in the current package
package_dir = Path(__file__).resolve().parent

for item in package_dir.iterdir():
    modulename = item.name.split('.')[0]
    if not modulename.startswith('_'):
        module = import_module(modulename)


def _import_all_modules():
    """ Dynamically imports all modules in this package. """
    import traceback
    import os
    global __all__
    __all__ = []
    globals_, locals_ = globals(), locals()

    # package_dir = os.path.dirname(os.path.realpath(__file__))

    package_dir = Path(__file__).resolve().parent
    # print(package_dir.name.lower())
    for path in package_dir.iterdir():
        print(path)
        if path.is_file():
            modulename = path.name.split('.')[0]
            # print(modulename)
            module = import_module(modulename)

            for name in module.__dict__:
                __all__.append(name)
        if path.is_dir():
            test = path.name.split('.')[0]
            # print(test)
            # print(package_dir.name.lower())
            # if not test.startswith('_') and not test.lower() == package_dir.name.lower():
            #     print(test)


class BaseCharacter:
    # A generic character
    def __init__(self, parent):
        self.parent = parent
        self.role_name = "Character"
        self.isPoisoned = False
        self.refresh()

    def refresh(self):
        pass

    def extra_info(self):
        return ""

class Outsider(BaseCharacter):

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Outsider"
