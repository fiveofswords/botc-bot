import discord, os, time, pickle, sys, asyncio, pytz, datetime
from config import *
from dateutil.parser import parse

### Classes
class Game():

    def __init__(self, seatingOrder, seatingOrderMessage, script):
        self.days = []
        self.isDay = False
        self.script = script
        self.seatingOrder = seatingOrder
        self.seatingOrderMessage = seatingOrderMessage
        if script.isAtheist:
            for person in game.seatingOrder:
                if gamemasterRole in server.get_member(message.author.id).roles:
                    person = person
                    break
            self.seatingOrder.insert(0, Player(Storyteller(), 'neutral', person))
            self.reseat()

    async def end(self, winner):
        # Ends the game

        # remove roles
        for person in self.seatingOrder:
            await person.wipe_roles()

        # unpin messages
        for msg in await channel.pins():
            if msg.created_at >= self.seatingOrderMessage.created_at:
                await msg.unpin()

        # announcement
        await channel.send('{}, {} has won. Good game!'.format(playerRole.mention, winner.lower()))

        # save backup
        i = 0
        while True:
            i += 1
            if not os.path.isfile('game_{}.pckl'.format(str(i))):
                break
        backup('game_{}.pckl'.format(str(i)))

        # delete old backup
        remove_backup('current_game.pckl')

        # turn off
        global game
        game = None
        await update_presence(client)

    async def reseat(self, newSeatingOrder):
        # Reseats the table

        # Seating order
        self.seatingOrder = newSeatingOrder

        # Seating order message
        messageText = '**Seating Order:**'
        for index, person in enumerate(self.seatingOrder):

            if person.isGhost:
                if person.deadVotes <= 0:
                    messageText += '\n{}'.format('~~' + person.nick + '~~ X')
                else:
                    messageText += '\n{}'.format('~~' + person.nick + '~~ ' + 'O' * person.deadVotes)

            else:
                messageText += '\n{}'.format(person.nick)

            if isinstance(person.character, SeatingOrderModifier):
                messageText += person.character.seating_order_message(self.seatingOrder)

            person.position = index

        await self.seatingOrderMessage.edit(content=messageText)

    async def add_traveler(self, person):
        self.seatingOrder.insert(person.position, person)
        await person.user.add_roles(playerRole, travelerRole)
        await self.reseat(self.seatingOrder)
        await channel.send('{} has joined the town as the {}.'.format(person.nick, person.character.role_name))

    async def remove_traveler(self, person):
        self.seatingOrder.remove(person)
        await person.user.remove_roles(playerRole, travelerRole)
        await self.reseat(self.seatingOrder)
        announcement = await channel.send('{} has left the town.'.format(person.nick))
        await announcement.pin()

    async def start_day(self, kills=[]):
        for person in kills:
            await person.kill()
        if kills == [] and len(self.days) > 0:
            await channel.send('No one has died.')
        await channel.send('{}, wake up!'.format(playerRole.mention))
        self.days.append(Day())
        self.isDay = True
        await update_presence(client)
        for person in game.seatingOrder:
            await person.morning()
            if isinstance(person.character, DayStartModifier):
                person.character.on_day_start()

class Script():
    # Stores booleans for characters which modify the game rules from the script

    def __init__(self, scriptList):
        self.isAtheist = 'atheist' in scriptList
        self.list = scriptList

class Day():
    # Stores information about a specific day

    def __init__(self):
        self.isExecutionToday = False
        self.isNoms = False
        self.isPms = True
        self.votes = []
        self.voteEndMessages = []
        self.deadlineMessages = []
        self.skipMessages = []
        self.aboutToDie = None

    async def open_pms(self):
        # Opens PMs
        self.isPms = True
        for memb in gamemasterRole.members:
            await memb.send('PMs are now open.')
        await update_presence(client)

    async def open_noms(self):
        # Opens nominations
        self.isNoms = True
        if len(self.votes) == 0:
            for person in game.seatingOrder:
                if isinstance(person.character, NomsCalledModifier):
                    person.character.on_noms_called()
        for memb in gamemasterRole.members:
            await memb.send('Nominations are now open.')
        await update_presence(client)

    async def close_pms(self):
        # Closes PMs
        self.isPms = False
        for memb in gamemasterRole.members:
            await memb.send('PMs are now closed.')
        await update_presence(client)

    async def close_noms(self):
        # Closes nominations
        self.isNoms = False
        for memb in gamemasterRole.members:
            await memb.send('Nominations are now closed.')
        await update_presence(client)

    async def nomination(self,nominee,nominator):
        await self.close_pms()
        await self.close_noms()
        nominee.canBeNominated = False
        if isinstance(nominee.character, Traveler):
            self.votes.append(TravelerVote(nominee, nominator))
            announcement = await channel.send('{} has called for {}\'s exile.'.format(nominator.nick if nominator else 'The storytellers', nominee.user.mention))
        else:
            if nominator:
                nominator.canNominate = False
            self.votes.append(Vote(nominee, nominator))
            announcement = await channel.send('{} has been nominated by {}.'.format(nominee.user.mention, nominator.nick if nominator else 'the storytellers'))
        self.votes[-1].announcements.append(announcement.id)
        await announcement.pin()
        await self.votes[-1].call_next()

    async def end(self):
        # Ends the day

        for person in game.seatingOrder:
            if isinstance(person.character, DayEndModifier):
                person.character.on_day_end()

        for msg in self.voteEndMessages:
            await (await channel.fetch_message(msg)).unpin()

        for msg in self.deadlineMessages:
            await (await channel.fetch_message(msg)).unpin()

        for msg in self.skipMessages:
            await (await channel.fetch_message(msg)).unpin()

        game.isDay = False
        self.isNoms = False
        self.isPms = False

        if not self.isExecutionToday:
            await channel.send('No one was executed.')

        await channel.send('{}, go to sleep!'.format(playerRole.mention))

class Vote():
    # Stores information about a specific vote

    def __init__(self, nominee, nominator):
        self.nominee = nominee
        self.nominator = nominator
        self.order = game.seatingOrder[game.seatingOrder.index(self.nominee)+1:] + game.seatingOrder[:game.seatingOrder.index(self.nominee)+1]
        self.votes = 0
        self.voted = []
        self.history = []
        self.announcements = []
        self.presetVotes = {}
        self.values = {person: (0,1) for person in self.order}
        self.majority = 0.0
        for person in game.seatingOrder:
            if not person.isGhost:
                self.majority += 0.5
        for person in game.seatingOrder:
            if isinstance(person.character, VoteBeginningModifier):
                self.order, self.values, self.majority = person.character.on_vote_beginning(self.order, self.values, self.majority)
        self.position = 0
        game.days[-1].votes.append(self)
        self.done = False

    async def call_next(self):
        # Calls for person to vote

        toCall = self.order[self.position]
        for person in game.seatingOrder:
            if isinstance(person.character, VoteModifier):
                person.character.before_vote_call(toCall)
        if toCall.isGhost and toCall.deadVotes < 1:
            await self.vote(0)
            return
        if toCall in self.presetVotes:
            await self.vote(self.presetVotes[toCall])
            return
        await channel.send('{}, your vote on {}.'.format(toCall.user.mention, self.nominee.nick if self.nominee else 'the storytellers'))

    async def vote(self, vt, operator=None):
        # Executes a vote. vt is binary -- 0 if no, 1 if yes

        # Voter
        voter = self.order[self.position]

        # Check dead votes
        if vt == 1 and voter.isGhost and voter.deadVotes < 1:
            if not st:
                await voter.user.send('You do not have any dead votes. Please vote no.')
            else:
                await operator.send('{} does not have any dead votes. They must vote no.'.format(voter.nick))
            return
        if vt == 1 and voter.isGhost:
            await voter.remove_dead_vote()

        # On vote character powers
        for person in game.seatingOrder:
            if isinstance(person.character, VoteModifier):
                person.character.on_vote()

        # Vote tracking
        self.history.append(vt)
        self.votes += self.values[voter][vt]
        if vt == 1:
            self.voted.append(voter)

        # Announcement
        text = 'yes' if vt == 1 else 'no'
        self.announcements.append((await channel.send('{} votes {}. {} votes.'.format(voter.nick, text, str(self.votes)))).id)
        await (await channel.fetch_message(self.announcements[-1])).pin()

        # Next vote
        self.position += 1
        if self.position == len(self.order):
            await self.end_vote()
            return
        await self.call_next()

    async def end_vote(self):
        # When the vote is over
        tie = False
        if self.votes >= self.majority:
            aboutToDie = game.days[-1].aboutToDie
            if aboutToDie == None:
                dies = True
            elif self.votes > aboutToDie[1].votes:
                dies = True
            elif self.votes == aboutToDie[1].votes:
                dies = False
                tie = True
            else:
                dies = False
        else:
            dies = False
        for person in game.seatingOrder:
            if isinstance(person.character, VoteModifier):
                dies, tie = person.character.on_vote_conclusion(dies, tie)
        if len(self.voted) == 0:
            text = 'no one'
        elif len(self.voted) == 1:
            text = self.voted[0].nick
        elif len(self.voted) == 2:
            text = self.voted[0].nick + ' and ' + self.voted[1].nick
        else:
            text = ', '.join([x.nick for x in self.voted[:-1]]) + ', and ' + self.voted[-1].nick
        if dies:
            if aboutToDie != None:
                msg = await channel.fetch_message(game.days[-1].voteEndMessages[game.days[-1].votes.index(aboutToDie[1])])
                await msg.edit(content=msg.content[:-31] + ' They are not about to be executed.')
            game.days[-1].aboutToDie = (self.nominee, self)
            announcement = await channel.send('{} votes on {} (nominated by {}): {}. They are about to be executed.'.format(str(self.votes), self.nominee.nick if self.nominee else 'the storytellers', self.nominator.nick if self.nominator else 'the storytellers', text))
        elif tie:
            if aboutToDie != None:
                msg = await channel.fetch_message(game.days[-1].voteEndMessages[game.days[-1].votes.index(aboutToDie[1])])
                await msg.edit(content=msg.content[:-31] + ' No one is about to be executed.')
            game.days[-1].aboutToDie = None
            announcement = await channel.send('{} votes on {} (nominated by {}): {}. No one is about to be executed.'.format(str(self.votes), self.nominee.nick if self.nominee else 'the storytellers', self.nominator.nick if self.nominator else 'the storytellers', text))
        else:
            announcement = await channel.send('{} votes on {} (nominated by {}): {}. They are not about to be executed.'.format(str(self.votes), self.nominee.nick if self.nominee else 'the storytellers', self.nominator.nick if self.nominator else 'the storytellers', text))

        await announcement.pin()
        game.days[-1].voteEndMessages.append(announcement.id)

        for msg in self.announcements:
            await (await channel.fetch_message(msg)).unpin()

        self.done = True

        await game.days[-1].open_noms()
        await game.days[-1].open_pms()

    async def preset_vote(self, person, vt, operator=None):
        # Check dead votes
        if vt == 1 and person.isGhost and person.deadVotes < 1:
            if not operator:
                await person.user.send('You do not have any dead votes. Please vote no.')
            else:
                await operator.send('{} does not have any dead votes. They must vote no.'.format(voter.nick))
            return

        self.presetVotes[person] = vt


    async def cancel_preset(self, person):
        del self.presetVotes[person]


    async def delete(self):
        # Undoes an unintentional nomination

        if self.nominator:
            self.nominator.canNominate = True
        if self.nominee:
            self.nominee.canBeNominated = True
        await channel.send('Nomination canceled!')

        for msg in self.announcements:
            await (await channel.fetch_message(msg)).unpin()

        self.done = True

        game.days[-1].votes.remove(self)

class TravelerVote():
    # Stores information about a specific call for exile

    def __init__(self, nominee, nominator):
        self.nominee = nominee
        self.nominator = nominator
        self.order = game.seatingOrder[game.seatingOrder.index(self.nominee)+1:] + game.seatingOrder[:game.seatingOrder.index(self.nominee)+1]
        self.votes = 0
        self.voted = []
        self.history = []
        self.announcements = []
        self.presetVotes = {}
        self.values = {person: (0,1) for person in self.order}
        self.majority = len(game.seatingOrder)/2
        self.position = 0
        game.days[-1].votes.append(self)
        self.done = False

    async def call_next(self):
        # Calls for person to vote

        toCall = self.order[self.position]
        if toCall.isGhost and toCall.deadVotes < 1:
            await self.vote(0)
            return
        if toCall in self.presetVotes:
            await self.vote(self.presetVotes[toCall])
            return
        await channel.send('{}, your vote on {}.'.format(toCall.user.mention, self.nominee.nick if self.nominee else 'the storytellers'))

    async def vote(self, vt, operator=None):
        # Executes a vote. vt is binary -- 0 if no, 1 if yes

        # Voter
        voter = self.order[self.position]

        # Vote tracking
        self.history.append(vt)
        self.votes += self.values[voter][vt]
        if vt == 1:
            self.voted.append(voter)

        # Announcement
        text = 'yes' if vt == 1 else 'no'
        self.announcements.append((await channel.send('{} votes {}. {} votes.'.format(voter.nick, text, str(self.votes)))).id)
        await (await channel.fetch_message(self.announcements[-1])).pin()

        # Next vote
        self.position += 1
        if self.position == len(self.order):
            await self.end_vote()
            return
        await self.call_next()

    async def end_vote(self):
        # When the vote is over
        if len(self.voted) == 0:
            text = 'no one'
        elif len(self.voted) == 1:
            text = self.voted[0].nick
        elif len(self.voted) == 2:
            text = self.voted[0].nick + ' and ' + self.voted[1].nick
        else:
            text = ', '.join([x.nick for x in self.voted[:-1]]) + ', and ' + self.voted[-1].nick
        if self.votes >= self.majority:
            announcement = await channel.send('{} votes on {} (nominated by {}): {}.'.format(str(self.votes), self.nominee.nick if self.nominee else 'the storytellers', self.nominator.nick if self.nominator else 'the storytellers', text))
        else:
            announcement = await channel.send('{} votes on {} (nominated by {}): {}. They are not exiled.'.format(str(self.votes), self.nominee.nick if self.nominee else 'the storytellers', self.nominator.nick if self.nominator else 'the storytellers', text))

        await announcement.pin()
        game.days[-1].voteEndMessages.append(announcement.id)

        for msg in self.announcements:
            await (await channel.fetch_message(msg)).unpin()

        self.done = True

        await game.days[-1].open_noms()
        await game.days[-1].open_pms()

    async def preset_vote(self, person, vt, operator=None):
        self.presetVotes[person] = vt

    async def cancel_preset(self, person):
        del self.presetVotes[person]

    async def delete(self):
        # Undoes an unintentional nomination

        if self.nominator:
            self.nominator.canNominate = True
        if self.nominee:
            self.nominee.canBeNominated = True
        channel.send('Nomination canceled.')

        for msg in self.announcements:
            await (await channel.fetch_message(msg)).unpin()

        self.done = True

        game.days[-1].votes.remove(self)

class Player():
    # Stores information about a player

    def __init__(self, character, alignment, user, position=None):
        self.character = character
        self.alignment = alignment
        self.user = user
        self.name = user.name
        self.nick = user.nick if user.nick else user.name
        self.position = position
        self.isGhost = False
        self.deadVotes = 1
        self.isActive = False
        self.canNominate = False
        self.canBeNominated = False
        self.hasSkipped = False
        self.messageHistory = []

        if inactiveRole in self.user.roles:
            self.isInactive = True
        else:
            self.isInactive = False

    def __getstate__(self):
        state = self.__dict__.copy()
        state['user'] = self.user.id
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.user = server.get_member(self.user)

    async def morning(self):
        if inactiveRole in self.user.roles:
            self.isInactive = True
        else:
            self.isInactive = False
        self.canNominate = True
        self.canBeNominated = True
        self.isActive = self.isInactive
        self.hasSkipped = self.isInactive

    async def kill(self, suppress = False):
        self.isGhost = True
        for person in game.seatingOrder:
            if isinstance(person, DeathModifier):
                person.on_death(self)
        if not suppress:
            announcement = await channel.send('{} has died.'.format(self.user.mention))
            await announcement.pin()
        await self.user.add_roles(ghostRole, deadVoteRole)
        await game.reseat(game.seatingOrder)

    async def execute(self, user):
        # Executes the player

        msg = await user.send('Do they die? yes or no')

        try:
            choice = await client.wait_for('message', check=(lambda x: x.author==user and x.channel==msg.channel), timeout=200)
        except asyncio.TimeoutError:
            await user.send('Message timed out!')
            return

        # Cancel
        if choice.content.lower() == 'cancel':
            await user.send('Action cancelled!')
            return

        # Yes
        if choice.content.lower() == 'yes' or choice.content.lower() == 'y':
            die = True

        # No
        elif choice.content.lower() == 'no' or choice.content.lower() == 'n':
            die = False

        else:
            await user.send('Your answer must be \'yes,\' \'y,\' \'no,\' or \'n\' exactly.')
            return

        msg = await user.send('Does the day end? yes or no')

        try:
            choice = await client.wait_for('message', check=(lambda x: x.author==user and x.channel==msg.channel), timeout=200)
        except asyncio.TimeoutError:
            await user.send('Message timed out!')
            return

        # Cancel
        if choice.content.lower() == 'cancel':
            await user.send('Action cancelled!')
            return

        # Yes
        if choice.content.lower() == 'yes' or choice.content.lower() == 'y':
            end = True

        # No
        elif choice.content.lower() == 'no' or choice.content.lower() == 'n':
            end = False

        else:
            await user.send('Your answer must be \'yes,\' \'y,\' \'no,\' or \'n\' exactly.')
            return

        if die:
            announcement = await channel.send('{} has been executed.'.format(self.user.mention))
            await announcement.pin()
            await self.kill(suppress=True)
        else:
            await channel.send('{} has been executed, but does not die.'.format(self.user.mention))
        game.days[-1].isExecutionToday = True
        if end:
            if game.isDay:
                await game.days[-1].end()

    async def revive(self):
        self.isGhost = False
        announcement = await channel.send('{} has come back to life.'.format(self.user.mention))
        await announcement.pin()
        await self.user.remove_roles(ghostRole, deadVoteRole)
        await game.reseat(game.seatingOrder)

    async def change_character(self, character):
        self.character = character
        await game.reseat(game.seatingOrder)

    async def change_alignment(self, alignment):
        self.alignment = alignment

    async def message(self, frm, content, jump):
        # Sends a message

        try:
            message = await self.user.send('Message from {}: **{}**'.format(frm.nick, content))
        except discord.errors.HTTPException:
            await frm.user.send('Message is too long.')
            return

        message_to = {'from': frm, 'to': self, 'content': content, 'day': len(game.days), 'time': message.created_at, 'jump': message.jump_url}
        message_from = {'from': frm, 'to': self, 'content': content, 'day': len(game.days), 'time': message.created_at, 'jump': jump}
        self.messageHistory.append(message_to)
        frm.messageHistory.append(message_from)

        for user in gamemasterRole.members:
            if user != self.user:
                await user.send('**[**{} **>** {}**]** {}'.format(frm.nick, self.nick, content))

        await channel.send('**{}** > **{}**'.format(frm.nick, self.nick))

        await frm.user.send('Message sent!')
        return

    async def make_inactive(self):
        self.isInactive = True
        await self.user.add_roles(inactiveRole)
        self.hasSkipped = True
        self.isActive = True

        if game.isDay:

            notActive = [player for player in game.seatingOrder if player.isActive == False]
            if len(notActive) == 1:
                for memb in gamemasterRole.members:
                    await memb.send('Just waiting on {} to speak.'.format(notActive[0].nick))
            if len(notActive) == 0:
                for memb in gamemasterRole.members:
                    await memb.send('Everyone has spoken!')

            canNominate = [player for player in game.seatingOrder if player.canNominate == True and player.hasSkipped == False]
            if len(canNominate) == 1:
                for memb in gamemasterRole.members:
                    await memb.send('Just waiting on {} to nominate or skip.'.format(canNominate[0].nick))
            if len(canNominate) == 0:
                for memb in gamemasterRole.members:
                    await memb.send('Everyone has nominated or skipped!')

    async def undo_inactive(self):
        self.isInactive = False
        await self.user.remove_roles(inactiveRole)
        self.hasSkipped = False

    async def add_dead_vote(self):
        if self.deadVotes == 0:
            await self.user.add_roles(deadVoteRole)
        self.deadVotes += 1
        await game.reseat(game.seatingOrder)

    async def remove_dead_vote(self):
        if self.deadVotes == 1:
            await self.user.remove_roles(deadVoteRole)
        self.deadVotes += -1
        await game.reseat(game.seatingOrder)

    async def wipe_roles(self):
        await self.user.remove_roles(travelerRole, ghostRole, deadVoteRole)

class Character():
    # A generic character
    def __init__(self):
        self.role_name = 'Character'

class Townsfolk(Character):
    # A generic townsfolk

    def __init__(self):
        super().__init__()
        self.role_name = 'Townsfolk'

class Outsider(Character):
    # A generic outsider

    def __init__(self):
        super().__init__()
        self.role_name = 'Outsider'

class Minion(Character):
    # A generic minion

    def __init__(self):
        super().__init__()
        self.role_name = 'Minion'

class Demon(Character):
    # A generic demon

    def __init__(self):
        super().__init__()
        self.role_name = 'Demon'

class SeatingOrderModifier(Character):
    # A character which modifies the seating order or seating order message

    def __init__(self):
        super().__init__()

    def seating_order(self, seatingOrder):
        # returns a seating order after the character's modifications
        return seatingOrder

    def seating_order_message(self, seatingOrder):
        # returns a string to be added to the seating order message specifically (not just to the seating order)
        return ''

class DayStartModifier(Character):
    # A character which modifies the start of the day

    def __init__(self):
        super().__init__()

    def on_day_start(self):
        # Called on the start of the day
        pass

class NomsCalledModifier(Character):
    # A character which modifies the start of the day

    def __init__(self):
        super().__init__()

    def on_noms_called(self):
        # Called when nominations are called for the first time each day
        pass

class NominationModifier(Character):
    # A character which triggers on a nomination

    def __init__(self):
        super().__init__()

    def on_nomination(self, nominator, nominee):
        # Called when a nomination is made
        pass

class DayEndModifier(Character):
    # A character which modifies the start of the day

    def __init__(self):
        super().__init__()

    def on_day_end(self):
        # Called on the end of the day
        pass

class VoteBeginningModifier(Character):
    # A character which modifies the value of players' votes

    def __init__(self):
        super().__init__()

    def modify_vote_values(self, order, values, majority):
        # returns a list of the vote's order, a dictionary of vote values, and majority
        return order, values, majority

class VoteModifier(Character):
    # A character which modifies the effect of votes

    def __init__(self):
        super().__init__()

    def on_vote_call(self, toCall):
        # Called every time a player is called to vote
        pass

    def on_vote(self):
        # Called every time a player votes
        pass

    def on_vote_conclusion(self, dies, tie):
        # returns boolean -- whether the nominee is about to die, whether the vote is tied
        return dies, tie

class DeathModifier(Character):
    # A character which triggers on a player's death

    def __init__(self):
        super().__init__()

    def on_death(self, person):
        # Called on death
        pass

class Traveler(SeatingOrderModifier):
    # A generic traveler

    def __init__(self):
        super().__init__()
        self.role_name = 'Traveler'

    def seating_order_message(self, seatingOrder):
        return ' - {}'.format(self.role_name)

    async def exile(self, person, user):

        msg = await user.send('Do they die? yes or no')

        try:
            choice = await client.wait_for('message', check=(lambda x: x.author==user and x.channel==msg.channel), timeout=200)
        except asyncio.TimeoutError:
            await user.send('Message timed out!')
            return

        # Cancel
        if choice.content.lower() == 'cancel':
            await user.send('Action cancelled!')
            return

        # Yes
        if choice.content.lower() == 'yes' or choice.content.lower() == 'y':
            die = True

        # No
        elif choice.content.lower() == 'no' or choice.content.lower() == 'n':
            die = False

        if die:
            announcement = await channel.send('{} has been exiled.'.format(person.user.mention))
            await announcement.pin()
            await person.kill(suppress=True)
        else:
            await channel.send('{} has been exiled, but does not die.'.format(person.user.mention))
        await person.user.add_roles(travelerRole)

class Storyteller(Character):
    # The storyteller

    def __init__(self):
        super().__init__()
        self.role_name = 'Storyteller'

class Chef(Townsfolk):
    # The chef

    def __init__(self):
        super().__init__()
        self.role_name = 'Chef'

class Empath(Townsfolk):
    # The empath

    def __init__(self):
        super().__init__()
        self.role_name = 'Empath'

class Investigator(Townsfolk):
    # The investigator

    def __init__(self):
        super().__init__()
        self.role_name = 'Investigator'

class FortuneTeller(Townsfolk):
    # The fortune teller

    def __init__(self):
        super().__init__()
        self.role_name = 'Fortune Teller'

class Librarian(Townsfolk):
    # The librarian

    def __init__(self):
        super().__init__()
        self.role_name = 'Librarian'

class Mayor(Townsfolk):
    # The mayor

    def __init__(self):
        super().__init__()
        self.role_name = 'Mayor'

class Monk(Townsfolk):
    # The monk

    def __init__(self):
        super().__init__()
        self.role_name = 'Monk'

class Slayer(Townsfolk):
    # The slayer

    def __init__(self):
        super().__init__()
        self.role_name = 'Slayer'

class Soldier(Townsfolk):
    # The soldier

    def __init__(self):
        super().__init__()
        self.role_name = 'Soldier'

class Ravenkeeper(Townsfolk):
    # The ravenkeeper

    def __init__(self):
        super().__init__()
        self.role_name = 'Ravenkeeper'

class Undertaker(Townsfolk):
    # The undertaker

    def __init__(self):
        super().__init__()
        self.role_name = 'Undertaker'

class Washerwoman(Townsfolk):
    # The washerwoman

    def __init__(self):
        super().__init__()
        self.role_name = 'Washerwoman'

class Virgin(Townsfolk):
    # The virgin

    def __init__(self):
        super().__init__()
        self.role_name = 'Virgin'

class Chambermaid(Townsfolk):
    # The chambermaid

    def __init__(self):
        super().__init__()
        self.role_name = 'Chambermaid'

class Exorcist(Townsfolk):
    # The exorcist

    def __init__(self):
        super().__init__()
        self.role_name = 'Exorcist'

class Gambler(Townsfolk):
    # The gambler

    def __init__(self):
        super().__init__()
        self.role_name = 'Gambler'

class Gossip(Townsfolk):
    # The gossip

    def __init__(self):
        super().__init__()
        self.role_name = 'Gossip'

class Grandmother(Townsfolk):
    # The grandmother

    def __init__(self):
        super().__init__()
        self.role_name = 'Grandmother'

class Innkeeper(Townsfolk):
    # The innkeeper

    def __init__(self):
        super().__init__()
        self.role_name = 'Innkeeper'

class Minstrel(Townsfolk):
    # The minstrel

    def __init__(self):
        super().__init__()
        self.role_name = 'Minstrel'

class Pacifist(Townsfolk):
    # The pacifist

    def __init__(self):
        super().__init__()
        self.role_name = 'Pacifist'

class Professor(Townsfolk):
    # The professor

    def __init__(self):
        super().__init__()
        self.role_name = 'Professor'

class Sailor(Townsfolk):
    # The sailor

    def __init__(self):
        super().__init__()
        self.role_name = 'Sailor'

class TeaLady(Townsfolk):
    # The tea lady

    def __init__(self):
        super().__init__()
        self.role_name = 'Tea Lady'

class Artist(Townsfolk):
    # The artist

    def __init__(self):
        super().__init__()
        self.role_name = 'Artist'

class Clockmaker(Townsfolk):
    # The clockmaker

    def __init__(self):
        super().__init__()
        self.role_name = 'Clockmaker'

class Dreamer(Townsfolk):
    # The dreamer

    def __init__(self):
        super().__init__()
        self.role_name = 'Dreamer'

class Flowergirl(Townsfolk):
     # The flowergirl

     def __init__(self):
         super().__init__()
         self.role_name = 'Flowergirl'

class Juggler(Townsfolk):
     # The juggler

     def __init__(self):
         super().__init__()
         self.role_name = 'Juggler'

class Mathematician(Townsfolk):
     # The mathematician

     def __init__(self):
         super().__init__()
         self.role_name = 'Mathematician'

class Oracle(Townsfolk):
    # The oracle

    def __init__(self):
        super().__init__()
        self.role_name = 'Oracle'

class Philosopher(Townsfolk):
    # The philosopher

    def __init__(self):
        super().__init__()
        self.role_name = 'Philosopher'

class Sage(Townsfolk):
    # The sage

    def __init__(self):
        super().__init__()
        self.role_name = 'Sage'

class Savant(Townsfolk):
    # The savant

    def __init__(self):
        super().__init__()
        self.role_name = 'Savant'

class Seamstress(Townsfolk):
    # The seamstress

    def __init__(self):
        super().__init__()
        self.role_name = 'Seamstress'

class SnakeCharmer(Townsfolk):
     # The snake charmer

     def __init__(self):
         super().__init__()
         self.role_name = 'Snake Charmer'

class TownCrier(Townsfolk):
    # The town crier

    def __init__(self):
        super().__init__()
        self.role_name = 'Town Crier'

class Farmer(Townsfolk):
    # The farmer

    def __init__(self):
        super().__init__()
        self.role_name = 'Farmer'

class Fisherman(Townsfolk):
    # The fisherman

    def __init__(self):
        super().__init__()
        self.role_name = 'Fisherman'

class General(Townsfolk):
    # The general

    def __init__(self):
        super().__init__()
        self.role_name = 'General'

class Knight(Townsfolk):
    # The knight

    def __init__(self):
        super().__init__()
        self.role_name = 'Knight'

class PoppyGrower(Townsfolk):
    # The poppy grower

    def __init__(self):
        super().__init__()
        self.role_name = 'Poppy Grower'

# amnesiac, atheist

class Drunk(Outsider):
    # The drunk

    def __init__(self):
        super().__init__()
        self.role_name = 'Drunk'

class Butler(Outsider):
    # The butler

    def __init__(self):
        super().__init__()
        self.role_name = 'Butler'

class Saint(Outsider):
    # The saint

    def __init__(self):
        super().__init__()
        self.role_name = 'Saint'

class Recluse(Outsider):
    # The recluse

    def __init__(self):
        super().__init__()
        self.role_name = 'Recluse'

class Regent(Outsider):
    # The regent

    def __init__(self):
        super().__init__()
        self.role_name = 'Regent'

class Lunatic(Outsider):
    # The lunatic

    def __init__(self):
        super().__init__()
        self.role_name = 'Lunatic'

class Tinker(Outsider):
    # The tinker

    def __init__(self):
        super().__init__()
        self.role_name = 'Tinker'

class Barber(Outsider):
    # The barber

    def __init__(self):
        super().__init__()
        self.role_name = 'Barber'

class Klutz(Outsider):
    # The klutz

    def __init__(self):
        super().__init__()
        self.role_name = 'Klutz'

class Mutant(Outsider):
    # The mutant

    def __init__(self):
        super().__init__()
        self.role_name = 'Mutant'

class Sweetheart(Outsider):
    # The sweetheart

    def __init__(self):
        super().__init__()
        self.role_name = 'Sweetheart'

class Godfather(Minion):
    # The godfather

    def __init__(self):
        super().__init__()
        self.role_name = 'Godfather'

class Mastermind(Minion):
    # The mastermind

    def __init__(self):
        super().__init__()
        self.role_name = 'Mastermind'

class Spy(Minion):
    # The spy

    def __init__(self):
        super().__init__()
        self.role_name = 'Spy'

class Witch(Minion):
    # The witch

    def __init__(self):
        super().__init__()
        self.role_name = 'Witch'

class FangGu(Demon):
    # The fang gu

    def __init__(self):
        super().__init__()
        self.role_name = 'Fang Gu'

class Imp(Demon):
    # The imp

    def __init__(self):
        super().__init__()
        self.role_name = 'Imp'

class NoDashii(Demon):
    # The no dashii

    def __init__(self):
        super().__init__()
        self.role_name = 'No Dashii'

class Po(Demon):
    # The po

    def __init__(self):
        super().__init__()
        self.role_name = 'Po'

class Beggar(Traveler):
    # the beggar

    def __init__(self):
        super().__init__()
        self.role_name = 'Beggar'

class Gunslinger(Traveler):
    # the gunslinger

    def __init__(self):
        super().__init__()
        self.role_name = 'Gunslinger'

class Scapegoat(Traveler):
    # the scapegoat

    def __init__(self):
        super().__init__()
        self.role_name = 'Scapegoat'

class Apprentice(Traveler):
    # the apprentice

    def __init__(self):
        super().__init__()
        self.role_name = 'Apprentice'

class Matron(Traveler):
    # the matron

    def __init__(self):
        super().__init__()
        self.role_name = 'Matron'

class Judge(Traveler):
    # the judge

    def __init__(self):
        super().__init__()
        self.role_name = 'Judge'

class Bishop(Traveler):
    # the bishop

    def __init__(self):
        super().__init__()
        self.role_name = 'bishop'

class Butcher(Traveler):
    # the butcher

    def __init__(self):
        super().__init__()
        self.role_name = 'Butcher'

class BoneCollector(Traveler):
    # the bone collector

    def __init__(self):
        super().__init__()
        self.role_name = 'Bone Collector'

class Harlot(Traveler):
    # the harlot

    def __init__(self):
        super().__init__()
        self.role_name = 'Harlot'

class Barista(Traveler):
    # the barista

    def __init__(self):
        super().__init__()
        self.role_name = 'Barista'

class Deviant(Traveler):
    # the deviant

    def __init__(self):
        super().__init__()
        self.role_name = 'Deviant'

class Gangster(Traveler):
    # the gangster

    def __init__(self):
        super().__init__()
        self.role_name = 'Gangster'


### API Stuff
client = discord.Client() # discord client

# Read API Token
with open(os.path.dirname(os.path.realpath(__file__))+'/token.txt') as tokenfile:
    TOKEN = tokenfile.readline().strip()


### Functions
def str_to_class(str):
    return getattr(sys.modules[__name__], str)

async def generate_possibilities(text, people):
    # Generates possible users with name or nickname matching text

    possibilities = []
    for person in people:
        if ((person.nick != None and text.lower() in person.nick.lower()) or text.lower() in person
        .name.lower()):
            possibilities.append(person)
    return possibilities

async def choices(user, possibilities, text):
    # Clarifies which user is indended when there are multiple matches

    # Generate clarification message
    if text == '':
        messageText = 'Who do you mean? or use \'cancel\''
    else:
        messageText = 'Who do you mean by {}? or use \'cancel\''.format(text)
    for index,person in enumerate(possibilities):
        messageText += '\n({}). {}'.format(index + 1, person.nick if person.nick else person.name)

    # Request clarifciation from user
    reply = await user.send(messageText)
    try:
        choice = await client.wait_for('message', check=(lambda x: x.author==user and x.channel==reply.channel), timeout=200)
    except asyncio.TimeoutError:
        await user.send('Timed out.')
        return

    # Cancel
    if choice.content.lower() == 'cancel':
        await user.send('Action cancelled!')
        return

    # If a is an int
    try:
        a = possibilities[int(choice.content)-1]
        return possibilities[int(choice.content)-1]

    # If a is a name
    except Exception:
        return await select_player(user, choice.content, possibilities)

async def select_player(user, text, possibilities):
    # Finds a player from players matching a string

    new_possibilities = await generate_possibilities(text, possibilities)

    # If no users found
    if len(new_possibilities) == 0:
        await user.send('User {} not found. Try again!'.format(text))
        return

    # If exactly one user found
    elif len(new_possibilities) == 1:
        return new_possibilities[0]

    # If too many users found
    elif len(new_possibilities) > 1:
        return await choices(user, new_possibilities, text)

async def yes_no(user, text):
    # Ask a yes or no question of a user

    reply = await user.send('{}? yes or no'.format(text))
    try:
        choice = await client.wait_for('message', check=(lambda x: x.author==user and x.channel==reply.channel), timeout=200)
    except asyncio.TimeoutError:
        await user.send('Timed out.')
        return

    # Cancel
    if choice.content.lower() == 'cancel':
        await user.send('Action cancelled!')
        return

    # Yes
    if choice.content.lower() == 'yes' or choice.content.lower() == 'y':
        return True

    # No
    elif choice.content.lower() == 'no' or choice.content.lower() == 'n':
        return False

    else:
        return await user.send('Your answer must be \'yes,\' \'y,\' \'no,\' or \'n\' exactly. Try again.')
        return await yes_no(user, text)

async def get_player(user):
    # returns the Player object corresponding to user
    if game == None:
        return

    for person in game.seatingOrder:
        if person.user == user:
            return person

    return None

async def make_active(user):
    # Makes user active

    if not await get_player(user):
        return

    person = await get_player(user)

    if person.isActive == True:
        return

    person.isActive = True
    notActive = [player for player in game.seatingOrder if player.isActive == False]
    if len(notActive) == 1:
        for memb in gamemasterRole.members:
            await memb.send('Just waiting on {} to speak.'.format(notActive[0].nick))
    if len(notActive) == 0:
        for memb in gamemasterRole.members:
            await memb.send('Everyone has spoken!')

async def cannot_nominate(user):
    # Uses user's nomination

    (await get_player(user)).canNominate = False
    canNominate = [player for player in game.seatingOrder if player.canNominate == True and player.hasSkipped == False]
    if len(canNominate) == 1:
        for memb in gamemasterRole.members:
            await memb.send('Just waiting on {} to nominate or skip.'.format(canNominate[0].nick))
    if len(canNominate) == 0:
        for memb in gamemasterRole.members:
            await memb.send('Everyone has nominated or skipped!')

async def update_presence(client):
    # Updates Discord Presence

    if game == None:
        await client.change_presence(status = discord.Status.dnd, activity = discord.Game(name = 'No ongoing game!'))
    elif game.isDay == False:
        await client.change_presence(status = discord.Status.idle, activity = discord.Game(name = 'It\'s nighttime!'))
    else:
        clopen = ['Closed', 'Open']
        await client.change_presence(status = discord.Status.online, activity = discord.Game(name = 'PMs {}, Nominations {}!'.format(clopen[game.days[-1].isPms],clopen[game.days[-1].isNoms])))

def backup(fileName):
# Backs up the game state

    objects = [x for x in dir(game) if not x.startswith('__') and not callable(getattr(game,x))]
    with open(fileName, 'wb') as file:
        pickle.dump(objects, file)

    for obj in objects:
        with open(obj+'_'+fileName, 'wb') as file:
            if obj == 'seatingOrderMessage':
                pickle.dump(getattr(game, obj).id, file)
            else:
                pickle.dump(getattr(game, obj), file)

async def load(fileName):
# Loads the game state

    with open(fileName, 'rb') as file:
        objects = pickle.load(file)

    game = Game([], None, Script([]))
    for obj in objects:
        if not os.path.isfile(obj+'_'+fileName):
            print('Incomplete backup found.')
            return
        with open(obj+'_'+fileName, 'rb') as file:
            if obj == 'seatingOrderMessage':
                id = pickle.load(file)
                msg = await channel.fetch_message(id)
                setattr(game, obj, msg)
            else:
                setattr(game, obj, pickle.load(file))

    return game

def remove_backup(fileName):

    os.remove(fileName)
    for obj in [x for x in dir(game) if not x.startswith('__') and not callable(getattr(game,x))]:
        os.remove(obj+'_'+fileName)

def is_dst():

    x = datetime.datetime(datetime.datetime.now().year, 1, 1, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern')) # Jan 1 of this year
    y = datetime.datetime.now(pytz.timezone('US/Eastern'))
    return (y.utcoffset() != x.utcoffset())

### Event Handling
@client.event
async def on_ready():
    # On startup

    global server, channel, playerRole, travelerRole, ghostRole, deadVoteRole, gamemasterRole, inactiveRole, game
    game = None

    server = client.get_guild(serverid)
    channel = client.get_channel(channelid)

    for role in server.roles:
        if role.name == playerName:
            playerRole = role
        elif role.name == travelerName:
            travelerRole = role
        elif role.name == ghostName:
            ghostRole = role
        elif role.name == deadVoteName:
            deadVoteRole = role
        elif role.name == gamemasterName:
            gamemasterRole = role
        elif role.name == inactiveName:
            inactiveRole = role

    if os.path.isfile('current_game.pckl'):
        game = await load('current_game.pckl')
        print('Backup restored!')

    else:
        print('No backup found.')

    await update_presence(client)
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
async def on_message(message):
    # Handles messages
    global game

    # Don't respond to self
    if message.author == client.user:
        return

    # Update activity
    if message.channel == channel:
        if game != None:
            if game.isDay:
                await make_active(message.author)
                if game != None:
                    backup('current_game.pckl')

        # Votes
        if '@vote' in message.content.lower() or ',vote' in message.content.lower():

            argument = message.content.lower()[message.content.lower().index('vote ')+5:]

            if game == None:
                await channel.send('There\'s no game right now.')
                return

            if game.isDay == False:
                await channel.send('It\'s not day right now.')
                return

            if game.days[-1].votes == [] or game.days[-1].votes[-1].done == True:
                await channel.send('There\'s no vote right now.')
                return

            if argument != 'yes' and argument != 'y' and argument != 'no' and argument != 'n':
                await channel.send('{} is not a valid vote. Use \'yes\', \'y\', \'no\', or \'n\'.'.format(argument))
                return

            vote = game.days[-1].votes[-1]

            if vote.order[vote.position] != await get_player(message.author):
                await channel.send('It\'s not your vote right now.')
                return

            vt = int(argument == 'yes' or argument == 'y')

            await vote.vote(vt)
            if game != None:
                backup('current_game.pckl')
            return

    # Responding to dms
    if message.guild == None:

        # Check if command
        if message.content.startswith('@') or message.content.startswith(','):

            # Generate command and arguments
            if ' ' in message.content:
                # VERY DANGEROUS TESTING COMMAND
                if message.content[1:message.content.index(' ')].lower() == 'exec':
                    if message.author.id == 149969652141785088:
                        exec(message.content[message.content.index(' ') + 1:])
                        return
                command = message.content[1:message.content.index(' ')].lower()
                argument = message.content[message.content.index(' ') + 1:].lower()
            else:
                command = message.content[1:].lower()
                argument = ''

            # Opens pms
            if command == 'openpms':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to open PMs.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s not day right now.')
                    return

                await game.days[-1].open_pms()
                if game != None:
                    backup('current_game.pckl')

            # Opens nominations
            elif command == 'opennoms':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to open nominations.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s not day right now.')
                    return

                await game.days[-1].open_noms()
                if game != None:
                    backup('current_game.pckl')

            # Opens pms and nominations
            elif command == 'open':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to open PMs and nominations.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s not day right now.')
                    return

                await game.days[-1].open_pms()
                await game.days[-1].open_noms()
                if game != None:
                    backup('current_game.pckl')

            # Closes pms
            elif command == 'closepms':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to close PMs.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s not day right now.')
                    return

                await game.days[-1].close_pms()
                if game != None:
                    backup('current_game.pckl')

            # Closes nominations
            elif command == 'closenoms':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to close nominations.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s not day right now.')
                    return

                await game.days[-1].close_noms()
                if game != None:
                    backup('current_game.pckl')

            # Closes pms and nominations
            elif command == 'close':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to close PMs and nominations.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s not day right now.')
                    return

                await game.days[-1].close_pms()
                await game.days[-1].close_noms()
                if game != None:
                    backup('current_game.pckl')
                return

            # Starts game
            elif command == 'startgame':

                if game != None:
                    await message.author.send('There\'s already an ongoing game!')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to start a game.')
                    return

                msg = await message.author.send('What is the seating order? (separate users with line breaks)')
                try:
                    order = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==msg.channel), timeout=200)
                except asyncio.TimeoutError:
                    await message.author.send('Timed out.')
                    return

                if order.content == 'cancel':
                    await message.author.send('Game cancelled!')
                    return

                order = order.content.split('\n')

                msg = await message.author.send('What are the corresponding roles? (also separated with line breaks)')
                try:
                    roles = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==msg.channel), timeout=200)
                except asyncio.TimeoutError:
                    await message.author.send('Timed out.')
                    return

                if roles.content == 'cancel':
                    await message.author.send('Game cancelled!')
                    return

                roles = roles.content.split('\n')

                if len(roles) != len(order):
                    await message.author.send('Players and roles do not match.')
                    return

                users = []
                for person in order:
                    name = await select_player(message.author, person, server.members)
                    if name == None:
                        return
                    users.append(name)

                characters = []
                for text in roles:
                    role = ''.join([''.join([y.capitalize() for y in x.split('-')]) for x in text.split(' ')])
                    try:
                        role = str_to_class(role)
                    except AttributeError:
                        await message.author.send('Role not found: {}.'.format(text))
                        return
                    characters.append(role)

                for index, user in enumerate(users):
                    await user.add_roles(playerRole)
                    if issubclass(characters[index], Traveler):
                        await user.add_roles(travelerRole)

                alignments = []
                for role in characters:
                    if issubclass(role, Traveler):
                        msg = await message.author.send('What alignment is the {}?'.format(role().role_name))
                        try:
                            alignment = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==msg.channel), timeout=200)
                        except asyncio.TimeoutError:
                            await message.author.send('Timed out.')
                            return

                        if alignment.content == 'cancel':
                            await message.author.send('Game cancelled!')
                            return

                        if alignment.content.lower() != 'good' and alignment.content.lower() != 'evil':
                            await message.author.send('The alignment must be \'good\' or \'evil\' exactly.')
                            return

                        alignments.append(alignment.content.lower())

                    elif issubclass(role, Townsfolk) or issubclass(role, Outsider):
                        alignments.append('good')

                    elif issubclass(role, Minion) or issubclass(role, Demon):
                        alignments.append('evil')

                indicies = [x for x in range(len(users))]

                seatingOrder = []
                for x in indicies:
                    seatingOrder.append(Player(characters[x](), alignments[x], users[x], x))

                msg = await message.author.send('What roles are on the script? (send the text of the json file from the script creator)')
                try:
                    script = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==msg.channel), timeout=200)
                except asyncio.TimeoutError:
                    await message.author.send('Timed out.')
                    return

                if script.content == 'cancel':
                    await message.author.send('Game cancelled!')
                    return

                scriptList = script.content[8:-3].split('"},{"id":"')

                script = Script(scriptList)

                # Role Stuff
                for memb in server.members:
                    print(memb)
                    if gamemasterRole in server.get_member(memb.id).roles:
                        pass
                    elif not memb in users:
                        await memb.remove_roles(playerRole, travelerRole, ghostRole, deadVoteRole)
                    elif isinstance(characters[users.index(memb)], Traveler):
                        await memb.remove_roles(ghostRole, deadVoteRole)
                    else:
                        await memb.remove_roles(travelerRole, ghostRole, deadVoteRole)

                await channel.send('{}, welcome to Blood on the Clocktower! Go to sleep.'.format(playerRole.mention))

                messageText = '**Seating Order:**'
                for person in seatingOrder:
                    messageText += '\n{}'.format(person.nick)
                    if isinstance(person.character, SeatingOrderModifier):
                        messageText += person.character.seating_order_message(seatingOrder)
                seatingOrderMessage = await channel.send(messageText)
                await seatingOrderMessage.pin()

                game = Game(seatingOrder, seatingOrderMessage, script)

                backup('current_game.pckl')
                await update_presence(client)

                return

            # Ends game
            elif command == 'endgame':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to end the game.')
                    return

                if argument.lower() != 'good' and argument.lower() != 'evil':
                    await message.author.send('The winner must be \'good\' or \'evil\' exactly.')
                    return

                await game.end(argument.lower())
                if game != None:
                    backup('current_game.pckl')
                return

            # Starts day
            elif command == 'startday':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to start the day.')
                    return

                if game.isDay == True:
                    await message.author.send('It\'s already day!')
                    return

                if argument == '':
                    await game.start_day()
                    if game != None:
                        backup('current_game.pckl')
                    return

                people = [await select_player(message.author, person, game.seatingOrder) for person in argument.split(' ')]
                if None in people:
                    return

                await game.start_day(people)
                if game != None:
                    backup('current_game.pckl')
                return

            # Ends day
            elif command == 'endday':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to end the day.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s already night!')
                    return

                await game.days[-1].end()
                if game != None:
                    backup('current_game.pckl')
                return

            # Kills a player
            elif command == 'kill':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to kill players.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                if person.isGhost:
                    await message.author.send('{} is already dead.'.format(person.nick))
                    return

                await person.kill()
                if game != None:
                    backup('current_game.pckl')
                return

            # Executes a player
            elif command == 'execute':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to execute players.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                await person.execute(message.author)
                if game != None:
                    backup('current_game.pckl')
                return

            # Exiles a traveler
            elif command == 'exile':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to exile travelers.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                if not isinstance(person.character, Traveler):
                    await message.author.send('{} is not a traveler.'.format(person.nick))

                await person.character.exile(person)
                if game != None:
                    backup('current_game.pckl')
                return

            # Revives a player
            elif command == 'revive':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to revive players.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                if not person.isGhost:
                    await message.author.send('{} is not dead.'.format(person.nick))
                    return

                await person.revive()
                if game != None:
                    backup('current_game.pckl')
                return

            # Changes role
            elif command == 'changerole':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to change roles.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                msg = await message.author.send('What is the new role?')
                try:
                    role = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==msg.channel), timeout=200)
                except asyncio.TimeoutError:
                    await message.author.send('Timed out.')
                    return

                role = role.content.lower()

                if role == 'cancel':
                    await message.author.send('Role change cancelled!')
                    return

                role = ''.join([''.join([y.capitalize() for y in x.split('-')]) for x in role.split(' ')])
                try:
                    role = str_to_class(role)
                except AttributeError:
                    await message.author.send('Role not found: {}.'.format(text))
                    return

                await person.change_character(role())
                await message.author.send('Role change successful!')
                if game != None:
                    backup('current_game.pckl')
                return

            # Changes alignment
            elif command == 'changealignment':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to change alignemtns.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                msg = await message.author.send('What is the new alignment?')
                try:
                    alignment = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==msg.channel), timeout=200)
                except asyncio.TimeoutError:
                    await message.author.send('Timed out.')
                    return

                alignment = alignment.content.lower()

                if alignment == 'cancel':
                    await message.author.send('Alignment change cancelled!')
                    return

                if alignment != 'good' and alignment != 'evil':
                    await message.author.send('The alignment must be \'good\' or \'evil\' exactly.')
                    return

                await person.change_alignment(alignment)
                await message.author.send('Alignment change successful!')
                if game != None:
                    backup('current_game.pckl')
                return

            # Marks as inactive
            elif command == 'makeinactive':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to make players inactive.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                await person.make_inactive()
                if game != None:
                    backup('current_game.pckl')
                return

            # Marks as inactive
            elif command == 'undoinactive':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to make players active.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                await person.undo_inactive()
                if game != None:
                    backup('current_game.pckl')
                return

            # Adds traveler
            elif command == 'addtraveler' or command == 'addtraveller':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to add travelers.')
                    return

                person = await select_player(message.author, argument, server.members)
                if person == None:
                    return

                if await get_player(person) != None:
                    await message.author.send('{} is already in the game.'.format(person.nick if person.nick else person.name))
                    return

                msg = await message.author.send('What role?')
                try:
                    text = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==msg.channel), timeout=200)
                except asyncio.TimeoutError:
                    await message.author.send('Timed out.')
                    return

                if text.content == 'cancel':
                    await message.author.send('Traveler cancelled!')
                    return

                text = text.content

                role = ''.join([''.join([y.capitalize() for y in x.split('-')]) for x in text.split(' ')])

                try:
                    role = str_to_class(role)
                except AttributeError:
                    await message.author.send('Role not found: {}.'.format(text))
                    return

                if not issubclass(role, Traveler):
                    await message.author.send('{} is not a traveler role.'.format(text))
                    return

                # Determine position in order
                msg = await message.author.send('Where in the order are they? (send the player before them or a one-indexed integer)')
                try:
                    pos = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==msg.channel), timeout=200)

                except asyncio.TimeoutError:
                    await message.author.send('Timed out.')
                    return

                if pos.content == 'cancel':
                    await message.author.send('Traveler cancelled!')
                    return

                pos = pos.content

                try:
                    pos = int(pos) - 1
                except ValueError:
                    player = await select_player(message.author, pos, game.seatingOrder)
                    if player == None:
                        return
                    pos = player.position + 1

                # Determine alignment
                msg = await message.author.send('What alignment are they?')
                try:
                    alignment = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==msg.channel), timeout=200)

                except asyncio.TimeoutError:
                    await message.author.send('Timed out.')
                    return

                if alignment.content == 'cancel':
                    await message.author.send('Game cancelled!')
                    return

                if alignment.content.lower() != 'good' and alignment.content.lower() != 'evil':
                    await message.author.send('The alignment must be \'good\' or \'evil\' exactly.')
                    return

                await game.add_traveler(Player(role(), alignment.content.lower(), person, pos))
                if game != None:
                    backup('current_game.pckl')
                return

            # Removes traveler
            elif command == 'removetraveler' or command == 'removetraveller':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to add travelers.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                await game.remove_traveler(person)
                if game != None:
                    backup('current_game.pckl')
                return

            # Changes seating chart
            elif command == 'reseat':

                if game == None:
                    await message.author.send('There\'s no game right now.')

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to change the seating chart.')
                    return

                msg = await message.author.send('What is the seating order? (separate users with line breaks)')
                try:
                    order = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==msg.channel), timeout=200)

                except asyncio.TimeoutError:
                    await message.author.send('Timed out.')
                    return

                if order.content == 'cancel':
                    await message.author.send('Game cancelled!')
                    return

                order = [await select_player(message.author, person, game.seatingOrder) for person in order.content.split('\n')]
                if None in order:
                    return

                await game.reseat(order)
                if game != None:
                    backup('current_game.pckl')
                return

            # Cancels a nomination
            elif command == 'cancelnomination':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to cancel nominations.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s not day right now.')
                    return

                if game.days[-1].votes == [] or game.days[-1].votes[-1].done == True:
                    await message.author.send('There\'s no vote right now.')
                    return

                await game.days[-1].votes[-1].delete()
                await game.days[-1].open_pms()
                await game.days[-1].open_noms()
                if game != None:
                    backup('current_game.pckl')
                return

            # Sets a deadline
            elif command == 'setdeadline':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to set deadlines.')
                    return

                try:
                    time = parse(argument)
                except ValueError:
                    await message.author.send('Time format not recognized. If in doubt, use \'HH:MM\'. All times must be in UTC.')
                    return

                if len(game.days[-1].deadlineMessages) > 0:
                    await (await channel.fetch_message(game.days[-1].deadlineMessages[-1])).unpin()

                if is_dst():
                    announcement = await channel.send('{}, nominations are open. The deadline is {} PDT / {} EDT / {} UTC unless someone nominates or everyone skips.'.format(playerRole.mention, time.astimezone(pytz.timezone('US/Pacific')).strftime('%-I:%M %p'), time.astimezone(pytz.timezone('US/Eastern')).strftime('%-I:%M %p'), time.astimezone(pytz.utc).strftime('%H:%M')))
                else:
                    announcement = await channel.send('{}, nominations are open. The deadline is {} PST / {} EST / {} UTC unless someone nominates or everyone skips.'.format(playerRole.mention, time.astimezone(pytz.timezone('US/Pacific')).strftime('%-I:%M %p'), time.astimezone(pytz.timezone('US/Eastern')).strftime('%-I:%M %p'), time.astimezone(pytz.utc).strftime('%H:%M')))
                await announcement.pin()
                game.days[-1].deadlineMessages.append(announcement.id)
                await game.days[-1].open_noms()

            # Gives a dead vote
            elif command == 'givedeadvote':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to give dead votes.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                await person.add_dead_vote()
                if game != None:
                    backup('current_game.pckl')
                return

            # Removes a dead vote
            elif command == 'removedeadvote':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to remove dead votes.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                await person.remove_dead_vote()
                if game != None:
                    backup('current_game.pckl')
                return

            # Clears history
            elif command == 'clear':
                await message.author.send('{}Clearing\n{}'.format('\u200B\n' * 25, '\u200B\n' * 25))
                return

            # Checks active players
            elif command == 'notactive':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s not day right now.')
                    return

                notActive = [player for player in game.seatingOrder if player.isActive == False]

                if notActive == []:
                    message.author.send('Everyone has spoken!')
                    return

                messageText = 'These players have not spoken:'
                for player in notActive:
                    messageText += '\n{}'.format(player.nick)

                await message.author.send(messageText)
                return

            # Checks who can nominate
            elif command == 'cannominate':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s not day right now.')
                    return

                canNominate = [player for player in game.seatingOrder if player.canNominate == True and player.hasSkipped == False]
                if canNominate == []:
                    message.author.send('Everyone has nominated or skipped!')
                    return

                messageText = 'These players have not nominated or skipped:'
                for player in canNominate:
                    messageText += '\n{}'.format(player.nick)

                await message.author.send(messageText)
                return

            # Checks who can be nominated
            elif command == 'canbenominated':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s not day right now.')
                    return

                canBeNominated = [player for player in game.seatingOrder if player.canBeNominated == True]
                if canBeNominated == []:
                    message.author.send('Everyone has been nominated!')
                    return

                messageText = 'These players have not been nominated:'
                for player in canBeNominated:
                    messageText += '\n{}'.format(player.nick)

                await message.author.send(messageText)
                return

            # Nominates
            elif command == 'nominate':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s not day right now.')
                    return

                if game.days[-1].isNoms == False:
                    await message.author.send('Nominations aren\'t open right now.')
                    return

                if not await get_player(message.author):
                    if not gamemasterRole in server.get_member(message.author.id).roles:
                        await message.author.send('You aren\'t in the game, and so cannot nominate.')
                        return

                if game.script.isAtheist:
                    if argument == 'storytellers' or argument == 'the storytellers' or gamemasterRole in server.get_member(message.author.id).roles:
                        for person in game.seatingOrder:
                            if isinstance(person.character, Storyteller):
                                await game.days[-1].nomination(person, await get_player(message.author))
                                if game != None:
                                    backup('current_game.pckl')
                                return

                person = await select_player(message.author, argument, game.seatingOrder)

                if gamemasterRole in server.get_member(message.author.id).roles:
                    await game.days[-1].nomination(person, None)
                    if game != None:
                        backup('current_game.pckl')
                    return

                await game.days[-1].nomination(person, await get_player(message.author))
                if game != None:
                    backup('current_game.pckl')
                return

            # Votes
            elif command == 'vote':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s not day right now.')
                    return

                if game.days[-1].votes == [] or game.days[-1].votes[-1].done == True:
                    await message.author.send('There\'s no vote right now.')
                    return

                if argument != 'yes' and argument != 'y' and argument != 'no' and argument != 'n':
                    await message.author.send('{} is not a valid vote. Use \'yes\', \'y\', \'no\', or \'n\'.'.format(argument))
                    return

                vote = game.days[-1].votes[-1]

                if gamemasterRole in server.get_member(message.author.id).roles:
                    msg = await message.author.send('Whose vote is this?')
                    try:
                        reply = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==msg.channel), timeout=200)

                    except asyncio.TimeoutError:
                        await message.author.send('Timed out.')
                        return

                    if reply.content.lower() == 'cancel':
                        await message.author.send('Vote cancelled!')
                        return

                    reply = reply.content.lower()

                    person = await select_player(message.author, reply, game.seatingOrder)
                    if person == None:
                        return

                    if vote.order[vote.position] != person:
                        await message.author.send('It\'s not their vote right now. Do you mean @presetvote?')
                        return

                    vt = int(argument == 'yes' or argument == 'y')

                    await vote.vote(vt, operator=message.author)
                    if game != None:
                        backup('current_game.pckl')
                    return

                if vote.order[vote.position] != await get_player(message.author):
                    await message.author.send('It\'s not your vote right now. Do you mean @presetvote?')
                    return

                vt = int(argument == 'yes' or argument == 'y')

                await vote.vote(vt)
                if game != None:
                    backup('current_game.pckl')
                return

            # Presets a vote
            elif command == 'presetvote':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s not day right now.')
                    return

                if game.days[-1].votes == [] or game.days[-1].votes[-1].done == True:
                    await message.author.send('There\'s no vote right now.')
                    return

                if argument != 'yes' and argument != 'y' and argument != 'no' and argument != 'n':
                    await message.author.send('{} is not a valid vote. Use \'yes\', \'y\', \'no\', or \'n\'.'.format(argument))
                    return

                vote = game.days[-1].votes[-1]

                if gamemasterRole in server.get_member(message.author.id).roles:
                    msg = await message.author.send('Whose vote is this?')
                    try:
                        reply = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==msg.channel), timeout=200)

                    except asyncio.TimeoutError:
                        await message.author.send('Timed out.')
                        return

                    if reply.content.lower() == 'cancel':
                        await message.author.send('Preset vote cancelled!')
                        return

                    reply = reply.content.lower()

                    person = await select_player(message.author, reply, game.seatingOrder)
                    if person == None:
                        return

                    vt = int(argument == 'yes' or argument == 'y')

                    await vote.preset_vote(person, vt, operator=message.author)
                    await message.author.send('Successfully preset!')
                    if game != None:
                        backup('current_game.pckl')
                    return

                vt = int(argument == 'yes' or argument == 'y')

                await vote.preset_vote(await get_player(message.author), vt)
                await message.author.send('Successfully preset! For more nuanced presets, contact the storytellers.')
                if game != None:
                    backup('current_game.pckl')
                return

            # Cancels a preset vote
            elif command == 'cancelpreset':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if game.isDay == False:
                    await message.author.send('It\'s not day right now.')
                    return

                if game.days[-1].votes == [] or game.days[-1].votes[-1].done == True:
                    await message.author.send('There\'s no vote right now.')
                    return

                vote = game.days[-1].votes[-1]

                if gamemasterRole in server.get_member(message.author.id).roles:
                    msg = await message.author.send('Whose vote do you want to cancel?')
                    try:
                        reply = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==msg.channel), timeout=200)

                    except asyncio.TimeoutError:
                        await message.author.send('Timed out.')
                        return

                    if reply.content.lower() == 'cancel':
                        await message.author.send('Cancelling preset cancelled!')
                        return

                    reply = reply.content.lower()

                    person = await select_player(message.author, reply, game.seatingOrder)
                    if person == None:
                        return

                    await vote.cancel_preset(person)
                    await message.author.send('Successfully canceled!')
                    if game != None:
                        backup('current_game.pckl')
                    return

                await vote.cancel_preset(await get_player(message.author))
                await message.author.send('Successfully canceled! For more nuanced presets, contact the storytellers.')
                if game != None:
                    backup('current_game.pckl')
                return

            # Sends pm
            elif command == 'pm' or command == 'message':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not game.isDay:
                    await message.author.send('It\'s not day right now.')
                    return

                if not game.days[-1].isPms: # Check if PMs open
                    await message.author.send('PMs are closed.')
                    return

                if not await get_player(message.author):
                    await message.author.send('You are not in the game. You may not send messages.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder + [x for x in server.members if gamemasterRole in x.roles])
                if person == None:
                    return

                if person not in game.seatingOrder:
                    person = Player(Storyteller(), 'neutral', person)

                messageText = 'Messaging {}. What would you like to send?'.format(person.nick)
                reply = await message.author.send(messageText)

                # Process reply
                try:
                    intendedMessage = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==reply.channel), timeout=200)

                # Timeout
                except asyncio.TimeoutError:
                    await message.author.send('Message timed out!')
                    return

                # Cancel
                if intendedMessage.content.lower() == 'cancel':
                    await message.author.send('Message canceled!')
                    return

                await person.message(await get_player(message.author), intendedMessage.content, message.jump_url)
                if not (await get_player(message.author)).isActive:
                    await make_active(message.author)
                if game != None:
                    backup('current_game.pckl')
                return

            # Replies to the previous message
            elif command == 'reply':

                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not game.isDay:
                    await message.author.send('It\'s not day right now.')
                    return

                if not game.days[-1].isPms: # Check if PMs open
                    await message.author.send('PMs are closed.')
                    return

                if not await get_player(message.author):
                    await message.author.send('You are not in the game. You may not send messages.')
                    return

                if len((await get_player(message.author)).messageHistory) == 0:
                    await message.author.send('You have no previous messages.')
                    return

                person = (await get_player(message.author)).messageHistory[-1]['from']

                messageText = 'Messaging {}. What would you like to send?'.format(person.nick)
                reply = await message.author.send(messageText)

                # Process reply
                try:
                    intendedMessage = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==reply.channel), timeout=200)

                # Timeout
                except asyncio.TimeoutError:
                    await message.author.send('Message timed out!')
                    return

                # Cancel
                if intendedMessage.content.lower() == 'cancel':
                    await message.author.send('Message canceled!')
                    return

                await person.message(await get_player(message.author), intendedMessage.content, message.jump_url)
                if not (await get_player(message.author)).isActive:
                    await make_active(message.author)
                if game != None:
                    backup('current_game.pckl')

                return

            # Message history
            elif command == 'history':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if gamemasterRole in server.get_member(message.author.id).roles:

                    argument = argument.split(', ')
                    if len(argument) != 2:
                        await message.author.send('There must be exactly two comma-separated inputs.')
                        return

                    person1 = await select_player(message.author, argument[0], game.seatingOrder)
                    if person1 == None:
                        return

                    person2 = await select_player(message.author, argument[1], game.seatingOrder)
                    if person2 == None:
                        return

                    messageText = '**History between {} and {} (Times in UTC):**\n\n**Day 1:**'.format(person1.nick, person2.nick)
                    day = 1
                    for msg in person1.messageHistory:
                        if not ((msg['from'] == person1 and msg['to'] == person2) or (msg['to'] == person1 and msg['from'] == person2)):
                            continue
                        if len(messageText) > 1500:
                            await message.author.send(messageText)
                            messageText = ''
                        while msg['day'] != day:
                            await message.author.send(messageText)
                            day += 1
                            messageText = '**Day {}:**'.format(str(day))
                        messageText += '\nFrom: {} | To: {} | Time: {}\n**{}**'.format(msg['from'].nick,msg['to'].nick,msg['time'].strftime("%m/%d, %H:%M:%S"),msg['content'])

                    await message.author.send(messageText)
                    return

                if not await get_player(message.author):
                    await message.author.send('You are not in the game. You have no message history.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                messageText = '**History with {} (Times in UTC):**\n\n**Day 1:**'.format(person.nick)
                day = 1
                for msg in (await get_player(message.author)).messageHistory:
                    if not msg['from'] == person and not msg['to'] == person:
                        continue
                    if len(messageText) > 1500:
                        await message.author.send(messageText)
                        messageText = ''
                    while msg['day'] != day:
                        await message.author.send(messageText)
                        day += 1
                        messageText = '\n\n**Day {}:**'.format(str(day))
                    messageText += '\nFrom: {} | To: {} | Time: {}\n**{}**'.format(msg['from'].nick,msg['to'].nick,msg['time'].strftime("%m/%d, %H:%M:%S"),msg['content'])

                await message.author.send(messageText)
                return

            # Help dialogue
            elif command == 'help':
                if gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('''**Storyteller Commands (multiple arguments are always comma-separated):**
startgame: starts the game
endgame <<team>>: ends the game, with winner team
openpms: opens pms
opennoms: opens nominations
open: opens pms and nominations
closepms: closes pms
closenoms: closes nominations
close: closes pms and nominations
startday <<players>>: starts the day, killing players
endday: ends the day. if there is an execution, execute is preferred
kill <<player>>: kills player
execute <<player>>: executes player
exile <<traveler>>: exiles traveler
revive <<player>>: revives player
changerole <<player>>: changes player's role
changealignment <<player>>: changes player's alignment
makeinactive <<player>>: marks player as inactive. must be done in all games player is participating in
undoinactive <<player>>: undoes an inactivity mark. must be done in all games player is participating in
addtraveler <<player>> or addtraveller <<player>>: adds player as a traveler
removetraveler <<traveler>> or removetraveller <<traveler>>: removes traveler from the game
reseat: reseats the game
cancelnomination: cancels the previous nomination
setdeadline <time>: sends a message with time in UTC as the deadline
givedeadvote <<player>>: adds a dead vote for player
removedeadvote <<player>>: removes a dead vote from player. not necessary for ordinary usage
history <<player1>> <<player2>>: views the message history between player1 and player2''')
                await message.author.send('''
**Player Commands:**
clear: returns whitespace
notactive: lists players who are yet to speak
cannominate: lists players who are yet to nominate or skip
canbenominated: lists players who are yet to be nominated
nominate <<player>>: nominates player
vote <<yes/no>>: votes on an ongoing nomination
presetvote <<yes/no>>: submits a preset vote. will not work if it is your turn to vote. not reccomended -- contact the storytellers instead
cancelpreset: cancels an existing preset
pm <<player>> or message <<player>>: sends player a message
reply: messages the authour of the previously received message
history <<player>>: views your message history with player
help: displays this dialogue''')
                return

            # Command unrecognized
            else:
                await message.author.send('Command {} not recognized. For a list of commands, type @help.'.format(command))


@client.event
async def on_message_edit(before, after):
    # Handles messages on modification
    if after.author == client.user:
        return


    # On pin
    if after.channel == channel and before.pinned == False and after.pinned == True:

        # Nomination
        if 'nominate ' in after.content.lower():

            argument = after.content.lower()[after.content.lower().index('nominate ') + 9:]

            if game == None:
                await channel.send('There\'s no game right now.')
                await after.unpin()
                return

            if game.isDay == False:
                await channel.send('It\'s not day right now.')
                await after.unpin()
                return

            if game.days[-1].isNoms == False:
                await channel.send('Nominations aren\'t open right now.')
                await after.unpin()
                return

            if not await get_player(after.author):
                await channel.send('You aren\'t in the game, and so cannot nominate.')
                await after.unpin()
                return

            if game.script.isAtheist:
                if argument == 'storytellers' or argument == 'the storytellers' or gamemasterRole in server.get_member(message.author.id).roles:
                    for person in game.seatingOrder:
                        if isinstance(person.character, Storyteller):
                            await game.days[-1].nomination(person, await get_player(message.author))
                            if game != None:
                                backup('current_game.pckl')
                            return

            names = await generate_possibilities(argument, game.seatingOrder)

            if len(names) == 1:

                await game.days[-1].nomination(names[0], await get_player(after.author))
                if game != None:
                    backup('current_game.pckl')
                return

            elif len(names) > 1:

                await channel.send('There are too many matching players.')
                await message.unpin()
                return

            else:

                await channel.send('There are no matching players.')
                await after.unpin()
                return

        # Skip
        elif 'skip' in after.content.lower():

            if game == None:
                await channel.send('There\'s no game right now.')
                await after.unpin()
                return

            if not await get_player(after.author):
                await channel.send('You aren\'t in the game, and so cannot nominate.')
                await after.unpin()
                return

            if not game.isDay:
                await channel.send('It\'s not day right now.')
                await after.unpin()
                return

            (await get_player(after.author)).hasSkipped = True
            if game != None:
                backup('current_game.pckl')

            canNominate = [player for player in game.seatingOrder if player.canNominate == True and player.hasSkipped == False]
            if len(canNominate) == 1:
                for memb in gamemasterRole.members:
                    await memb.send('Just waiting on {} to nominate or skip.'.format(canNominate[0].nick))
            if len(canNominate) == 0:
                for memb in gamemasterRole.members:
                    await memb.send('Everyone has nominated or skipped!')

            game.days[-1].skipMessages.append(after.id)

            return

    # On unpin
    elif after.channel == channel and before.pinned == True and after.pinned == False:

        # Unskip
        if 'skip' in after.content.lower():
            (await get_player(after.author)).hasSkipped = False
            if game != None:
                backup('current_game.pckl')


@client.event
async def on_member_update(before, after):
    # Handles member-level modifications

    if game != None:
        if await get_player(after):
            if before.nick != after.nick:
                (await get_player(after)).nick = after.nick
                await after.send('Your nickname has been updated.')
                backup('current_game.pckl')



### Event loop
while True:
    try:
        client.run(TOKEN)
        print('end')
        time.sleep(5)
    except Exception as e:
        print(str(e))
