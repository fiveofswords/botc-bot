from bot import NominationModifier
from characters.types.townsfolk import Townsfolk


class Virgin(Townsfolk, NominationModifier):
    # The virgin

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Virgin"

    def refresh(self):
        super().refresh()
        self.beenNominated = False

    async def on_nomination(self, nominee, nominator, proceed):
        # Returns bool -- whether the nomination proceeds
        # fixme: in debugging, nominee is equal to self.parent rather than self, fix this after kill is corrected to execute
        if nominee == self:
            if not self.beenNominated:
                self.beenNominated = True
                if isinstance(nominator.character, Townsfolk) and not self.isPoisoned:
                    if not nominator.isGhost:
                        # fixme: nominator should be executed rather than killed
                        await nominator.kill()
        return proceed
