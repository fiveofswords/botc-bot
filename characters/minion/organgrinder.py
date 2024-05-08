import itertools

from bot import NominationModifier, safe_send
from types.minion import Minion


class OrganGrinder(Minion, NominationModifier):
    # The organ grinder

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Organ Grinder"

    async def on_nomination(self, nominee, nominator, proceed):
        if not self.isPoisoned and not self.parent.isGhost:
            nominee_nick = nominator.nick if nominator else "the storytellers"
            nominator_mention = nominee.user.mention if nominee else "the storytellers"
            announcement = await safe_send(
                channel,
                "{}, {} has been nominated by {}. Organ Grinder is in play. Message your votes to the storytellers."
                .format(playerRole.mention, nominator_mention, nominee_nick),
            )
            await announcement.pin()
            this_day = game.days[-1]
            this_day.votes[-1].announcements.append(announcement.id)
            message_tally = {
                X: 0 for X in itertools.combinations(game.seatingOrder, 2)
            }

            has_had_multiple_votes = len(this_day.votes) > 1
            last_vote_message = None if not has_had_multiple_votes else await channel.fetch_message(
                this_day.votes[-2].announcements[0])
            for person in game.seatingOrder:
                for msg in person.messageHistory:
                    if msg["from"] == person:
                        if has_had_multiple_votes:
                            if msg["time"] >= last_vote_message.created_at:
                                if (person, msg["to"]) in message_tally:
                                    message_tally[(person, msg["to"])] += 1
                                elif (msg["to"], person) in message_tally:
                                    message_tally[(msg["to"], person)] += 1
                                else:
                                    message_tally[(person, msg["to"])] = 1
                        else:
                            if msg["day"] == len(game.days):
                                if (person, msg["to"]) in message_tally:
                                    message_tally[(person, msg["to"])] += 1
                                elif (msg["to"], person) in message_tally:
                                    message_tally[(msg["to"], person)] += 1
                                else:
                                    message_tally[(person, msg["to"])] = 1
            sorted_tally = sorted(message_tally.items(), key=lambda x: -x[1])
            messageText = "**Message Tally:**"
            for pair in sorted_tally:
                if pair[1] > 0:
                    messageText += "\n> {person1} - {person2}: {n}".format(
                        person1=pair[0][0].nick, person2=pair[0][1].nick, n=pair[1]
                    )
                else:
                    messageText += "\n> All other pairs: 0"
                    break
            await safe_send(channel, messageText)
            return False
        return proceed
