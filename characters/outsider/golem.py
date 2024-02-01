from bot import NominationModifier
from characters.types.demon import Demon
from characters.types.outsider import Outsider


class Golem(Outsider, NominationModifier):
    # The golem

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Golem"

    def refresh(self):
        super().refresh()
        self.hasNominated = False

    async def on_nomination(self, nominee, nominator, proceed):
        # fixme: golem instantly kills a recluse when it should be ST decision
        if nominator == self.parent:
            if (
                not isinstance(nominee.character, Demon)
                and not self.isPoisoned
                and not self.parent.isGhost
                and not self.hasNominated
            ):
                await nominee.kill()
            self.hasNominated = True
        return proceed
