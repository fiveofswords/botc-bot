import asyncio

from bot import NominationModifier, DayStartModifier, safe_send, client, select_player
from characters.types.minion import Minion


class Witch(Minion, NominationModifier, DayStartModifier):
    # The witch

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Witch"

    def refresh(self):
        super().refresh()
        self.witched = None

    async def on_day_start(self, origin, kills):
        # todo: consider minions killed by vigormortis as active
        if self.parent.isGhost == True or self.parent in kills:
            self.witched = None
            return True

        msg = await safe_send(origin, "Who is witched?")
        try:
            reply = await client.wait_for(
                "message",
                check=(lambda x: x.author == origin and x.channel == msg.channel),
                timeout=200,
            )
        except asyncio.TimeoutError:
            await safe_send(origin, "Timed out.")
            return False

        person = await select_player(origin, reply.content, game.seatingOrder)
        if person is None:
            return False

        self.witched = person
        return True

    async def on_nomination(self, nominee, nominator, proceed):
        if (
            self.witched
            and self.witched == nominator
            and not self.witched.isGhost
            and not self.parent.isGhost
            and not self.isPoisoned
        ):
            await self.witched.kill()
        return proceed

    def extra_info(self):
        if self.witched:
            return "Witched: {}".format(self.witched.nick)
