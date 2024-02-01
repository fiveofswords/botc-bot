import asyncio

from bot import DayStartModifier, DeathModifier, safe_send, client, select_player
from characters.types.minion import Minion


class Assassin(Minion, DayStartModifier, DeathModifier):
    # The assassin

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Assassin"

    def refresh(self):
        super().refresh()
        self.target = None

    def extra_info(self):
        return "Assassinated: {}".format(self.target and self.target.nick)

    async def on_day_start(self, origin, kills):
        if self.parent.isGhost or self.target or len(game.days) < 1:
            return True
        else:
            msg = await safe_send(origin, "Does {} use Assassin ability?".format(self.parent.nick))
            try:
                choice = await client.wait_for(
                    "message",
                    check=(lambda x: x.author == origin and x.channel == msg.channel),
                    timeout=200)

                # Cancel
                if choice.content.lower() == "cancel":
                    await safe_send(origin, "Action cancelled!")
                    return False

                # Yes
                if choice.content.lower() == "yes" or choice.content.lower() == "y":
                    msg = await safe_send(origin, "Who is Assassinated?")
                    player_choice = await client.wait_for(
                        "message",
                        check=(lambda x: x.author == origin and x.channel == msg.channel),
                        timeout=200)
                    # Cancel
                    if player_choice.content.lower() == "cancel":
                        await safe_send(origin, "Action cancelled!")
                        return False

                    assassination_target = await select_player(origin, player_choice.content, game.seatingOrder)
                    if assassination_target is None:
                        return False
                    self.target = assassination_target

                    if assassination_target not in kills:
                        kills.append(assassination_target)
                    return True

                # No
                elif choice.content.lower() == "no" or choice.content.lower() == "n":
                    return True
                else:
                    await safe_send(
                        origin, "Your answer must be 'yes,' 'y,' 'no,' or 'n' exactly."
                    )
                    return False
            except asyncio.TimeoutError:
                await safe_send(origin, "Message timed out!")
                return False

    def on_death(self, person, dies):
        if self.isPoisoned or self.parent.isGhost:
            return dies
        if person == self.target:
            return True
        return dies

    def on_death_priority(self):
        return DeathModifier.FORCES_KILL
