import inspect
from pathlib import Path
from importlib import import_module



# iterate through the modules in the current package
package_dir = Path(__file__).resolve().parent

for item in package_dir.iterdir():
    modulename = item.name.split('.')[0]
    if not modulename.startswith('_'):
        module = import_module(modulename)
        print(module)
        members = inspect.getmembers(module)

        for member in members:
            print(member)

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



