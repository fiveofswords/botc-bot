import discord, os, time, dill, sys, asyncio, pytz, datetime, weakref
import numpy as np
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
        self.storytellers = [Player(Storyteller, 'neutral', person) for person in gamemasterRole.members]

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

    async def start_day(self, kills=[], origin=None):

        for person in game.seatingOrder:
            await person.morning()
            if isinstance(person.character, DayStartModifier):
                if not await person.character.on_day_start(origin, kills):
                    return
        for person in kills:
            await person.kill()
        if kills == [] and len(self.days) > 0:
            await channel.send('No one has died.')
        await channel.send('{}, wake up!'.format(playerRole.mention))
        self.days.append(Day())
        self.isDay = True
        await update_presence(client)

class Script():
    # Stores booleans for characters which modify the game rules from the script

    def __init__(self, scriptList):
        self.isAtheist = 'atheist' in scriptList
        self.isWitch = 'witch' in scriptList
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
        if not nominee:
            self.votes.append(Vote(nominee, nominator))
            if self.aboutToDie != None:
                announcement = await channel.send('{}, the storytellers have been nominated by {}. {} to tie, {} to execute.'.format(playerRole.mention, nominator.nick if nominator else 'the storytellers', str(int(np.ceil(max(self.aboutToDie[1].votes, self.votes[-1].majority)))), str(int(np.ceil(self.aboutToDie[1].votes+1)))))
            else:
                announcement = await channel.send('{}, the storytellers have been nominated by {}. {} to execute.'.format(playerRole.mention, nominator.nick if nominator else 'the storytellers', str(int(np.ceil(self.votes[-1].majority)))))
            await announcement.pin()
            if nominator:
                nominator.canNominate = False
            proceed = True
            for person in game.seatingOrder:
                if isinstance(person.character, NominationModifier):
                    proceed = await person.character.on_nomination(nominee, nominator, proceed)
            if not proceed:
                await self.votes[-1].delete()
                return
        elif isinstance(nominee.character, Traveler):
            nominee.canBeNominated = False
            self.votes.append(TravelerVote(nominee, nominator))
            announcement = await channel.send('{}, {} has called for {}\'s exile. {} to exile.'.format(playerRole.mention, nominator.nick if nominator else 'The storytellers', nominee.user.mention, str(int(np.ceil(self.votes[-1].majority)))))
            await announcement.pin()
        else:
            nominee.canBeNominated = False
            self.votes.append(Vote(nominee, nominator))
            if self.aboutToDie != None:
                announcement = await channel.send('{}, {} has been nominated by {}. {} to tie, {} to execute.'.format(playerRole.mention, nominee.user.mention if not nominee.user in gamemasterRole.members else 'the storytellers', nominator.nick if nominator else 'the storytellers', str(int(np.ceil(max(self.aboutToDie[1].votes, self.votes[-1].majority)))), str(int(np.ceil(self.aboutToDie[1].votes+1)))))
            else:
                announcement = await channel.send('{}, {} has been nominated by {}. {} to execute.'.format(playerRole.mention, nominee.user.mention if not nominee.user in gamemasterRole.members else 'the storytellers', nominator.nick if nominator else 'the storytellers', str(int(np.ceil(self.votes[-1].majority)))))
            await announcement.pin()
            if nominator:
                nominator.canNominate = False
            proceed = True
            for person in game.seatingOrder:
                if isinstance(person.character, NominationModifier):
                    proceed = await person.character.on_nomination(nominee, nominator, proceed)
            if not proceed:
                await self.votes[-1].delete()
                return
        self.votes[-1].announcements.append(announcement.id)
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
        await update_presence(client)

class Vote():
    # Stores information about a specific vote

    def __init__(self, nominee, nominator):
        self.nominee = nominee
        self.nominator = nominator
        if self.nominee != None:
            self.order = game.seatingOrder[game.seatingOrder.index(self.nominee)+1:] + game.seatingOrder[:game.seatingOrder.index(self.nominee)+1]
        else:
            self.order = game.seatingOrder
        self.votes = 0
        self.voted = []
        self.history = []
        self.announcements = []
        self.presetVotes = {}
        self.values = {person: (0,1) for person in self.order}
        self.majority = 0.0
        for person in self.order:
            if not person.isGhost:
                self.majority += 0.5
        for person in game.seatingOrder:
            if isinstance(person.character, VoteBeginningModifier):
                self.order, self.values, self.majority = person.character.modify_vote_values(self.order, self.values, self.majority)
        self.position = 0
        game.days[-1].votes.append(self)
        self.done = False

    async def call_next(self):
        # Calls for person to vote

        toCall = self.order[self.position]
        for person in game.seatingOrder:
            if isinstance(person.character, VoteModifier):
                person.character.on_vote_call(toCall)
        if toCall.isGhost and toCall.deadVotes < 1:
            await self.vote(0)
            return
        if toCall.user.id in self.presetVotes:
            await self.vote(self.presetVotes[toCall.user.id])
            return
        await channel.send('{}, your vote on {}.'.format(toCall.user.mention, self.nominee.nick if self.nominee else 'the storytellers'))
        try:
            preferences = {}
            if os.path.isfile(os.path.dirname(os.getcwd()) + '/preferences.pckl'):
                with open(os.path.dirname(os.getcwd()) + '/preferences.pckl', 'rb') as file:
                    preferences = dill.load(file)
            default = preferences[toCall.user.id]['defaultvote']
            time = default[1]
            await toCall.user.send('Will enter a {} vote in {} minutes.'.format(['no', 'yes'][default[0]],str(int(default[1]/60))))
            for memb in gamemasterRole.members:
                await memb.send('{}\'s vote. Their default is {} in {} minutes.'.format(toCall.nick, ['no', 'yes'][default[0]],str(int(default[1]/60))))
            await asyncio.sleep(time)
            if toCall == self.order[self.position]:
                await self.vote(default[0])
        except KeyError:
            for memb in gamemasterRole.members:
                await memb.send('{}\'s vote. They have no default.'.format(toCall.nick))

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

        self.presetVotes[person.user.id] = vt

    async def cancel_preset(self, person):
        del self.presetVotes[person.user.id]

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
        self.majority = len(self.order)/2
        self.position = 0
        game.days[-1].votes.append(self)
        self.done = False

    async def call_next(self):
        # Calls for person to vote

        toCall = self.order[self.position]
        if toCall.isGhost and toCall.deadVotes < 1:
            await self.vote(0)
            return
        if toCall.user.id in self.presetVotes:
            await self.vote(self.presetVotes[toCall.user.id])
            return
        await channel.send('{}, your vote on {}.'.format(toCall.user.mention, self.nominee.nick if self.nominee else 'the storytellers'))
        try:
            preferences = {}
            if os.path.isfile(os.path.dirname(os.getcwd()) + '/preferences.pckl'):
                with open(os.path.dirname(os.getcwd()) + '/preferences.pckl', 'rb') as file:
                    preferences = dill.load(file)
            default = preferences[toCall.user.id]['defaultvote']
            time = default[1]
            await toCall.user.send('Will enter a {} vote in {} minutes.'.format(['no', 'yes'][default[0]],str(int(default[1]/60))))
            await asyncio.sleep(time)
            if toCall == self.order[self.position]:
                await self.vote(default[0])
            for memb in gamemasterRole.members:
                await memb.send('{}\'s vote. Their default is {} in {} minutes.'.format(toCall.nick, ['no', 'yes'][default[0]],str(int(default[1]/60))))
        except KeyError:
            for memb in gamemasterRole.members:
                await memb.send('{}\'s vote. They have no default.'.format(toCall.nick))

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
            announcement = await channel.send('{} votes on {} (nominated by {}): {}.'.format(str(self.votes), self.nominee.nick if self.nominees else 'the storytellers', self.nominator.nick if self.nominator else 'the storytellers', text))
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
        self.presetVotes[person.user.id] = vt

    async def cancel_preset(self, person):
        del self.presetVotes[person.user.id]

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
        self.character = character(self)
        self.alignment = alignment
        self.user = user
        self.name = user.name
        self.nick = user.nick if user.nick else user.name
        self.position = position
        self.isGhost = False
        self.deadVotes = 0
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
        self.canNominate = not self.isGhost
        self.canBeNominated = True
        self.isActive = self.isInactive
        self.hasSkipped = self.isInactive

    async def kill(self, suppress = False, force = False):
        dies = True
        self.isGhost = True
        self.deadVotes = 1
        for person in game.seatingOrder:
            if isinstance(person, DeathModifier):
                dies = person.on_death(self, dies)
        if not dies and not force:
            return dies
        if not suppress:
            announcement = await channel.send('{} has died.'.format(self.user.mention))
            await announcement.pin()
        await self.user.add_roles(ghostRole, deadVoteRole)
        await game.reseat(game.seatingOrder)
        return dies

    async def execute(self, user, force = False):
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
            die = await self.kill(suppress = True, force = force)
            if die:
                announcement = await channel.send('{} has been executed.'.format(self.user.mention))
                await announcement.pin()
            else:
                await channel.send('{} has been executed, but does not die.'.format(self.user.mention))
        else:
            await channel.send('{} has been executed, but does not die.'.format(self.user.mention))
        game.days[-1].isExecutionToday = True
        if end:
            if game.isDay:
                await game.days[-1].end()

    async def revive(self):
        self.isGhost = False
        self.deadVotes = 0
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

            notActive = [player for player in game.seatingOrder if player.isActive == False and player.alignment != 'neutral']
            if len(notActive) == 1:
                for memb in gamemasterRole.members:
                    await memb.send('Just waiting on {} to speak.'.format(notActive[0].nick))
            if len(notActive) == 0:
                for memb in gamemasterRole.members:
                    await memb.send('Everyone has spoken!')

            canNominate = [player for player in game.seatingOrder if player.canNominate == True and player.hasSkipped == False and player.alignment != 'neutral']
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
    def __init__(self, parent):
        self.parent = parent
        self.role_name = 'Character'
        self.isPoisoned = False

class Townsfolk(Character):
    # A generic townsfolk

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Townsfolk'

class Outsider(Character):
    # A generic outsider

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Outsider'

class Minion(Character):
    # A generic minion

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Minion'

class Demon(Character):
    # A generic demon

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Demon'

class SeatingOrderModifier(Character):
    # A character which modifies the seating order or seating order message

    def __init__(self, parent):
        super().__init__(parent)

    def seating_order(self, seatingOrder):
        # returns a seating order after the character's modifications
        return seatingOrder

    def seating_order_message(self, seatingOrder):
        # returns a string to be added to the seating order message specifically (not just to the seating order)
        return ''

class DayStartModifier(Character):
    # A character which modifies the start of the day

    def __init__(self, parent):
        super().__init__(parent)

    async def on_day_start(self, origin, kills):
        # Called on the start of the day
        return True

class NomsCalledModifier(Character):
    # A character which modifies the start of the day

    def __init__(self, parent):
        super().__init__(parent)

    def on_noms_called(self):
        # Called when nominations are called for the first time each day
        pass

class NominationModifier(Character):
    # A character which triggers on a nomination

    def __init__(self, parent):
        super().__init__(parent)

    async def on_nomination(self, nominee, nominator, proceed):
        # Returns bool -- whether the nomination proceeds
        return proceed

class DayEndModifier(Character):
    # A character which modifies the start of the day

    def __init__(self, parent):
        super().__init__(parent)

    def on_day_end(self):
        # Called on the end of the day
        pass

class VoteBeginningModifier(Character):
    # A character which modifies the value of players' votes

    def __init__(self, parent):
        super().__init__(parent)

    def modify_vote_values(self, order, values, majority):
        # returns a list of the vote's order, a dictionary of vote values, and majority
        return order, values, majority

class VoteModifier(Character):
    # A character which modifies the effect of votes

    def __init__(self, parent):
        super().__init__(parent)

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

    def __init__(self, parent):
        super().__init__(parent)

    def on_death(self, person, dies):
        # Returns bool -- does person die
        return dies

class AbilityModifier(SeatingOrderModifier, DayStartModifier, NomsCalledModifier, NominationModifier, DayEndModifier, VoteBeginningModifier, VoteModifier, DeathModifier):
    # A character which can have different abilities

    def __init__(self, parent):
        super().__init__(parent)
        self.abilities = []

    def add_ability(self, role):
        self.abilities.append(role(self.parent))

    def seating_order(self, seatingOrder):
        # returns a seating order after the character's modifications
        for role in self.abilities:
            if isinstance(role, SeatingOrderModifier):
                seatingOrder = role.seating_order(seatingOrder)
        return seatingOrder

    async def on_day_start(self, origin, kills):
        # Called on the start of the day
        if not self.isPoisoned:
            for role in self.abilities:
                if isinstance(role, DayStartModifier):
                    await role.on_day_start(origin, kills)

        return True

    def on_noms_called(self):
        # Called when nominations are called for the first time each day
        if not self.isPoisoned:
            for role in self.abilities:
                if isinstance(role, NomsCalledModifier):
                    role.on_noms_called()

    async def on_nomination(self, nominee, nominator, proceed):
        # Returns bool -- whether the nomination proceeds
        if not self.isPoisoned:
            for role in self.abilities:
                if isinstance(role, NominationModifier):
                    proceed = await role.on_nomination(nominee, nominator, proceed)
        return proceed

    def on_day_end(self):
        # Called on the end of the day
        if not self.isPoisoned:
            for role in self.abilities:
                if isinstance(role, DayEndModifier):
                    role.on_day_end()

    def modify_vote_values(self, order, values, majority):
        # returns a list of the vote's order, a dictionary of vote values, and majority
        if not self.isPoisoned:
            for role in self.abilities:
                if isinstance(role, VoteModifier):
                    order, values, majority = role.modify_vote_values(order, values, majority)
        return order, values, majority

    def on_vote_call(self, toCall):
        # Called every time a player is called to vote
        if not self.isPoisoned:
            for role in self.abilities:
                if isinstance(role, VoteModifier):
                    role.on_vote_call()

    def on_vote(self):
        # Called every time a player votes
        if not self.isPoisoned:
            for role in self.abilities:
                if isinstance(role, VoteModifier):
                    role.on_vote()

    def on_vote_conclusion(self, dies, tie):
        # returns boolean -- whether the nominee is about to die, whether the vote is tied
        if not self.isPoisoned:
            for role in self.abilities:
                if isinstance(role, VoteModifier):
                    dies, tie = role.on_vote_conclusion(dies, tie)
        return dies, tie

    def on_death(self, person, dies):
        # Returns bool -- does person die
        if not self.isPoisoned:
            for role in self.abilities:
                if isinstance(role, DeathModifier):
                    die, deadVotes = role.on_death(person, dies)
        return dies

class Traveler(SeatingOrderModifier):
    # A generic traveler

    def __init__(self, parent):
        super().__init__(parent)
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
            die = await person.kill(suppress=True)
            if die:
                announcement = await channel.send('{} has been exiled.'.format(person.user.mention))
                await announcement.pin()
            else:
                await channel.send('{} has been exiled, but does not die.'.format(person.user.mention))
        else:
            await channel.send('{} has been exiled, but does not die.'.format(person.user.mention))
        await person.user.add_roles(travelerRole)

class Storyteller(SeatingOrderModifier):
    # The storyteller

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Storyteller'

    def seating_order_message(self, seatingOrder):
        return ' - {}'.format(self.role_name)

class Chef(Townsfolk):
    # The chef

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Chef'

class Empath(Townsfolk):
    # The empath

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Empath'

class Investigator(Townsfolk):
    # The investigator

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Investigator'

class FortuneTeller(Townsfolk):
    # The fortune teller

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Fortune Teller'

class Librarian(Townsfolk):
    # The librarian

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Librarian'

class Mayor(Townsfolk):
    # The mayor

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Mayor'

class Monk(Townsfolk):
    # The monk

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Monk'

class Slayer(Townsfolk):
    # The slayer

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Slayer'

class Soldier(Townsfolk):
    # The soldier

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Soldier'

class Ravenkeeper(Townsfolk):
    # The ravenkeeper

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Ravenkeeper'

class Undertaker(Townsfolk):
    # The undertaker

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Undertaker'

class Washerwoman(Townsfolk):
    # The washerwoman

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Washerwoman'

class Virgin(Townsfolk, NominationModifier):
    # The virgin

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Virgin'
        self.beenNominated = False

    async def on_nomination(self, nominee, nominator, proceed):
        # Returns bool -- whether the nomination proceeds
        if nominee == self:
            if not self.beenNominated:
                if isinstance(nominator.character, Townsfolk) and not self.isPoisoned:
                    if not nominator.isGhost:
                        await nominator.kill()
                self.beenNominated = True
        return proceed

class Chambermaid(Townsfolk):
    # The chambermaid

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Chambermaid'

class Exorcist(Townsfolk):
    # The exorcist

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Exorcist'

class Fool(Townsfolk):
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Fool'

    def on_death(self, person, dies):
        if self.parent == person and not self.isPoisoned:
            return False
        return True

class Gambler(Townsfolk):
    # The gambler

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Gambler'

class Gossip(Townsfolk):
    # The gossip

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Gossip'

class Grandmother(Townsfolk):
    # The grandmother

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Grandmother'

class Innkeeper(Townsfolk):
    # The innkeeper

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Innkeeper'

class Minstrel(Townsfolk):
    # The minstrel

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Minstrel'

class Pacifist(Townsfolk):
    # The pacifist

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Pacifist'

class Professor(Townsfolk):
    # The professor

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Professor'

class Sailor(Townsfolk):
    # The sailor

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Sailor'

    def on_death(self, person, dies):
        if self.parent == person and not self.isPoisoned:
            return False
        return True

class TeaLady(Townsfolk, DeathModifier):
    # The tea lady

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Tea Lady'

    def on_death(self, person, dies):
        neighbor1 = game.seatingOrder[self.parent.position-1]
        neighbor2 = game.seatingOrder[self.parent.position+1]
        if neighbor1.alignment == 'good' and neighbor2.alignment == 'good' and (person == neighbor1 or person == neighbor2):
            return False
        return True

class Artist(Townsfolk):
    # The artist

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Artist'

class Clockmaker(Townsfolk):
    # The clockmaker

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Clockmaker'

class Dreamer(Townsfolk):
    # The dreamer

    def __init__(self, parent):
        super().__init__(parent)
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

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Oracle'

class Philosopher(Townsfolk):
    # The philosopher

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Philosopher'

class Sage(Townsfolk):
    # The sage

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Sage'

class Savant(Townsfolk):
    # The savant

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Savant'

class Seamstress(Townsfolk):
    # The seamstress

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Seamstress'

class SnakeCharmer(Townsfolk):
     # The snake charmer

     def __init__(self):
         super().__init__()
         self.role_name = 'Snake Charmer'

class TownCrier(Townsfolk):
    # The town crier

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Town Crier'

class Farmer(Townsfolk):
    # The farmer

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Farmer'

class Fisherman(Townsfolk):
    # The fisherman

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Fisherman'

class General(Townsfolk):
    # The general

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'General'

class Knight(Townsfolk):
    # The knight

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Knight'

class PoppyGrower(Townsfolk):
    # The poppy grower

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Poppy Grower'

class WitchHunter(Townsfolk):
    # The witch hunter

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Witch Hunter'

class Cannibal(Townsfolk, AbilityModifier):
    # The cannibal

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Cannibal'

    def add_ability(self, role):
        self.abilities = [role(self.parent)]

class Nightwatchman(Townsfolk):
    # The nightwatchman

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Nightwatchman'

class Balloonist(Townsfolk):
    # The balloonist

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Balloonist'

# UNFINISHED
class Atheist(Townsfolk):
    # The atheist

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Atheist'

class Amnesiac(Townsfolk):
    # The amnesiac

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Amnesiac'

# Outsiders

class Drunk(Outsider):
    # The drunk

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Drunk'
        self.isPoisoned = True

class Butler(Outsider):
    # The butler

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Butler'

class Saint(Outsider):
    # The saint

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Saint'

class Recluse(Outsider):
    # The recluse

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Recluse'

class Regent(Outsider):
    # The regent

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Regent'

class Lunatic(Outsider):
    # The lunatic

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Lunatic'
        self.isPoisoned = True

class Tinker(Outsider):
    # The tinker

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Tinker'

class Barber(Outsider):
    # The barber

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Barber'

class Klutz(Outsider):
    # The klutz

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Klutz'

class Mutant(Outsider):
    # The mutant

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Mutant'

class Sweetheart(Outsider):
    # The sweetheart

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Sweetheart'

class Golem(Outsider, NominationModifier):
    # The golem

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Golem'
        self.hasNominated = False

    async def on_nomination(self, nominee, nominator, proceed):
        if nominator == self.parent:
            if not isinstance(nominee.character, Demon) and not self.isPoisoned and not self.parent.isGhost and not self.hasNominated == True:
                await nominee.kill()
            self.hasNominated = True
        return proceed

class Godfather(Minion):
    # The godfather

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Godfather'

class Mastermind(Minion):
    # The mastermind

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Mastermind'

class Spy(Minion):
    # The spy

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Spy'

class Cerenovous(Minion):
    # The cerenovous

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Cerenovous'

class Marionette(Minion):
    # The marionette

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Marionette'
        self.isPoisoned = True

class Poisoner(Minion):
    # The poisoner

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Poisoner'

class Harpy(Minion):
    # The harpy

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Harpy'

class Widow(Minion):
    # The widow

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Widow'

class Witch(Minion, NominationModifier, DayStartModifier):
    # The witch

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Witch'
        self.witched = None

    async def on_day_start(self, origin, kills):

        if self.parent.isGhost == True or self.parent in kills:
            self.witched = None
            return True

        msg = await origin.send('Who is witched?')
        try:
            reply = await client.wait_for('message', check=(lambda x: x.author==origin and x.channel==msg.channel), timeout=200)
        except asyncio.TimeoutError:
            await origin.send('Timed out.')
            return

        person = await select_player(origin, reply.content, game.seatingOrder)
        if person == None:
            return

        self.witched = person
        return True

    async def on_nomination(self, nominee, nominator, proceed):
        if self.witched and self.witched == nominator and not self.witched.isGhost and not self.parent.isGhost and not self.isPoisoned:
            await self.witched.kill()
        return proceed

class FangGu(Demon):
    # The fang gu

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Fang Gu'

class Imp(Demon):
    # The imp

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Imp'

class NoDashii(Demon):
    # The no dashii

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'No Dashii'
        '''
        neighbor1 = game.seatingOrder[self.parent.position-1]
        while not isinstance(neighbor1.character, Townsfolk) or neighbor1.isGhost:
            neighbor1 = game.seatingOrder[neighbor1.position-1]
        neighbor2 = game.seatingOrder[self.parent.position+1]
        while not isinstance(neighbor2.character, Townsfolk) or neighbor2.isGhost:
            neighbor2 = game.seatingOrder[neighbor1.position+1]
        neighbor1.character.isPoisoned = True
        neighbor2.character.isPoisoned = True
        '''

class Po(Demon):
    # The po

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Po'

class Leviathan(Demon):
    # The leviathan

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Po'

class AlHadikiar(Demon):
    # the al-hadikiar

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Po'

class Beggar(Traveler):
    # the beggar

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Beggar'

class Gunslinger(Traveler):
    # the gunslinger

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Gunslinger'

class Scapegoat(Traveler):
    # the scapegoat

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Scapegoat'

class Apprentice(Traveler):
    # the apprentice

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Apprentice'

class Matron(Traveler):
    # the matron

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Matron'

class Judge(Traveler):
    # the judge

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Judge'

class Bishop(Traveler):
    # the bishop

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'bishop'

class Butcher(Traveler):
    # the butcher

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Butcher'

class BoneCollector(Traveler):
    # the bone collector

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Bone Collector'

class Harlot(Traveler):
    # the harlot

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Harlot'

class Barista(Traveler):
    # the barista

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Barista'

class Deviant(Traveler):
    # the deviant

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Deviant'

class Gangster(Traveler):
    # the gangster

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Gangster'

class Bureaucrat(Traveler, DayStartModifier, VoteBeginningModifier):
    # the bureaucrat

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Bureaucrat'
        self.target = None

    async def on_day_start(self, origin, kills):

        if self.parent.isGhost == True or self.parent in kills:
            self.target = None
            return True

        msg = await origin.send('Who is bureaucrated?')
        try:
            reply = await client.wait_for('message', check=(lambda x: x.author==origin and x.channel==msg.channel), timeout=200)
        except asyncio.TimeoutError:
            await origin.send('Timed out.')
            return

        person = await select_player(origin, reply.content, game.seatingOrder)
        if person == None:
            return

        self.target = person
        return True

    def modify_vote_values(self, order, values, majority):
        if self.target and not self.isPoisoned:
            values[self.target] = (values[self.target][0], values[self.target][1] * 3)
            for person in game.days[-1].votes[-1]:
                majority += values[person][1]/2.0

        return order, values, majority

class Thief(Traveler, DayStartModifier, VoteBeginningModifier):
    # the thief

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = 'Thief'
        self.target = None

    async def on_day_start(self, origin, kills):

        if self.parent.isGhost == True or self.parent in kills:
            self.target = None
            return True

        msg = await origin.send('Who is bureaucrated?')
        try:
            reply = await client.wait_for('message', check=(lambda x: x.author==origin and x.channel==msg.channel), timeout=200)
        except asyncio.TimeoutError:
            await origin.send('Timed out.')
            return

        person = await select_player(origin, reply.content, game.seatingOrder)
        if person == None:
            return

        self.target = person
        return True

    def modify_vote_values(self, order, values, majority):
        if self.target and not self.isPoisoned:
            values[self.target] = (values[self.target][0], values[self.target][1] * -1)
            for person in game.seatingOrder:
                if not person.isGhost and person.alignment != 'neutral':
                    majority += values[person][1]/2.0

        return order, values, majority


### API Stuff
client = discord.Client() # discord client

# Read API Token
with open(os.path.dirname(os.path.realpath(__file__))+'/token.txt') as tokenfile:
    TOKEN = tokenfile.readline().strip()


### Functions
def str_cleanup(str, chars):
    str = [str]
    for char in chars:
        list = []
        for x in str:
            for x in x.split(char):
                list.append(x)
        str = list
    return ''.join([x.capitalize() for x in str])

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
    for index, person in enumerate(possibilities):
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
    notActive = [player for player in game.seatingOrder if player.isActive == False and player.alignment != 'neutral']
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
# Backs up the game-state

    objects = [x for x in dir(game) if not x.startswith('__') and not callable(getattr(game,x))]
    with open(fileName, 'wb') as file:
        dill.dump(objects, file)

    for obj in objects:
        with open(obj+'_'+fileName, 'wb') as file:
            if obj == 'seatingOrderMessage':
                dill.dump(getattr(game, obj).id, file)
            else:
                dill.dump(getattr(game, obj), file)

async def load(fileName):
# Loads the game-state

    with open(fileName, 'rb') as file:
        objects = dill.load(file)

    game = Game([], None, Script([]))
    for obj in objects:
        if not os.path.isfile(obj+'_'+fileName):
            print('Incomplete backup found.')
            return
        with open(obj+'_'+fileName, 'rb') as file:
            if obj == 'seatingOrderMessage':
                id = dill.load(file)
                msg = await channel.fetch_message(id)
                setattr(game, obj, msg)
            else:
                setattr(game, obj, dill.load(file))

    return game

def remove_backup(fileName):

    os.remove(fileName)
    for obj in [x for x in dir(game) if not x.startswith('__') and not callable(getattr(game,x))]:
        os.remove(obj+'_'+fileName)

def is_dst():

    x = datetime.datetime(datetime.datetime.now().year, 1, 1, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern')) # Jan 1 of this year
    y = datetime.datetime.now(pytz.timezone('US/Eastern'))
    return (y.utcoffset() != x.utcoffset())

def find_all(p, s):

    i = s.find(p)
    while i != -1:
        yield i
        i = s.find(p, i+1)

async def aexec(code):
    # Make an async function with the code and `exec` it
    exec(
        f'async def __ex(): ' +
        ''.join(f'\n {l}' for l in code.split('\n'))
    )

    # Get `__ex` from local variables, call it and return the result
    return await locals()['__ex']()


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

    if game != None:
        backup('current_game.pckl')

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
        if message.content.startswith(prefixes):

            if ' ' in message.content:
                command = message.content[1:message.content.index(' ')].lower()
                argument = message.content[message.content.index(' ') + 1:].lower()
            else:
                command = message.content[1:].lower()
                argument = ''

            if command == 'vote':

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

                if vote.order[vote.position].user != (await get_player(message.author)).user:
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
        if message.content.startswith(prefixes):

            # Generate command and arguments
            if ' ' in message.content:
                # VERY DANGEROUS TESTING COMMAND
                if message.content[1:message.content.index(' ')].lower() == 'exec':
                    if message.author.id == 149969652141785088:
                        await aexec(message.content[message.content.index(' ') + 1:])
                        return
                command = message.content[1:message.content.index(' ')].lower()
                argument = message.content[message.content.index(' ') + 1:].lower()
            else:
                command = message.content[1:].lower()
                argument = ''

            try:
                preferences = {}
                if os.path.isfile(os.path.dirname(os.getcwd()) + '/preferences.pckl'):
                    with open(os.path.dirname(os.getcwd()) + '/preferences.pckl', 'rb') as file:
                        preferences = dill.load(file)
                command = preferences[message.author.id]['aliases'][command]
            except KeyError:
                pass

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

                users = []
                for person in order:
                    name = await select_player(message.author, person, server.members)
                    if name == None:
                        return
                    users.append(name)

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

                characters = []
                for text in roles:
                    role = str_cleanup(text, [',', ' ', '-', '\''])
                    try:
                        role = str_to_class(role)
                    except AttributeError:
                        await message.author.send('Role not found: {}.'.format(text))
                        return
                    characters.append(role)

                # Role Stuff
                rls = {playerRole, travelerRole, deadVoteRole, travelerRole}
                for memb in server.members:
                    print(memb)
                    if gamemasterRole in server.get_member(memb.id).roles:
                        pass
                    else:
                        for rl in set(server.get_member(memb.id).roles).intersection(rls):
                            await memb.remove_roles(rl)

                for index, user in enumerate(users):
                    await user.add_roles(playerRole)
                    if issubclass(characters[index], Traveler):
                        await user.add_roles(travelerRole)

                alignments = []
                for role in characters:
                    if issubclass(role, Traveler):
                        msg = await message.author.send('What alignment is the {}?'.format(role(None).role_name))
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
                    seatingOrder.append(Player(characters[x], alignments[x], users[x], x))

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
                    await game.start_day(origin=message.author)
                    if game != None:
                        backup('current_game.pckl')
                    return

                people = [await select_player(message.author, person, game.seatingOrder) for person in argument.split(' ')]
                if None in people:
                    return

                await game.start_day(kills=people,origin=message.author)
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

                await person.kill(force = True)
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

                await person.execute(message.author, force = True)
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

                role = str_cleanup(role, [',', ' ', '-', '\''])
                try:
                    role = str_to_class(role)
                except AttributeError:
                    await message.author.send('Role not found: {}.'.format(text))
                    return

                await person.change_character(role(person))
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

            # Adds an ability to an AbilityModifier character
            elif command == 'changeability':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to give abilities.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                if not isinstance(person.character, AbilityModifier):
                    await message.author.send('The {} cannot gain abilities.'.format(person.character.role_name))
                    return

                msg = await message.author.send('What is the new role?')
                try:
                    role = await client.wait_for('message', check=(lambda x: x.author==message.author and x.channel==msg.channel), timeout=200)
                except asyncio.TimeoutError:
                    await message.author.send('Timed out.')
                    return

                role = role.content.lower()

                if role == 'cancel':
                    await message.author.send('New ability cancelled!')
                    return

                role = str_cleanup(role, [',', ' ', '-', '\''])
                try:
                    role = str_to_class(role)
                except AttributeError:
                    await message.author.send('Role not found: {}.'.format(text))
                    return

                person.character.add_ability(role)
                await message.author.send('New ability added.')
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

                role = str_cleanup(text, [',', ' ', '-', '\''])

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

                await game.add_traveler(Player(role, alignment.content.lower(), person, pos))
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

            # Resets the seating chart
            elif command == 'resetseats':
                if game == None:
                    await message.author.send('There\'s no game right now.')

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to change the seating chart.')
                    return

                await game.reseat(game.seatingOrder)
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

                if order.content == 'none':
                    await game.reseat(game.seatingOrder)

                order = [await select_player(message.author, person, game.seatingOrder) for person in order.content.split('\n')]
                if None in order:
                    return

                await game.reseat(order)
                if game != None:
                    backup('current_game.pckl')
                return

            # Poisons
            elif command == 'poison':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to revive players.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                person.character.isPoisoned = True
                await message.author.send('Successfully poisoned {}!'.format(person.nick))
                return

            # Unpoisons
            elif command == 'unpoison':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to revive players.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                person.character.isPoisoned = False
                await message.author.send('Successfully unpoisoned {}!'.format(person.nick))
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

                game.days[-1].votes[-1].nominator.canNominate = True

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

            # Views relevant information about a player
            elif command == 'info':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to view player information.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

                await message.author.send('''Player: {}
Character: {}
Alignment: {}
Alive: {}
Dead Votes: {}
Poisoned: {}'''.format(person.nick, person.character.role_name, person.alignment, str(not person.isGhost), str(person.deadVotes), str(person.character.isPoisoned)))
                return

            # Views the grimoire
            elif command == 'grimoire':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if not gamemasterRole in server.get_member(message.author.id).roles:
                    await message.author.send('You don\'t have permission to view player information.')
                    return

                messageText = '**Grimoire:**'
                for player in game.seatingOrder:
                    messageText += '\n{}: {}'.format(player.nick, player.character.role_name)
                    if player.character.isPoisoned and player.isGhost:
                        messageText += ' (Poisoned, Dead)'
                    elif player.character.isPoisoned and not player.isGhost:
                        messageText += ' (Poisoned)'
                    elif not player.character.isPoisoned and player.isGhost:
                        messageText += ' (Dead)'

                await message.author.send(messageText)
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

                notActive = [player for player in game.seatingOrder if player.isActive == False and player.alignment != 'neutral']

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

                canNominate = [player for player in game.seatingOrder if player.canNominate == True and player.hasSkipped == False and player.alignment != 'neutral']
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
                    if argument == 'storytellers' or argument == 'the storytellers' or (len(await generate_possibilities(argument, server.members)) == 1 and gamemasterRole in server.get_member((await generate_possibilities(argument, server.members))[0].id).roles):
                        if None in [x.nominee for x in game.days[-1].votes]:
                            await message.author.send('The storytellers have already been nominated today.')
                            await after.unpin()
                            return
                        await game.days[-1].nomination(None, await get_player(message.author))
                        if game != None:
                            backup('current_game.pckl')
                        await message.unpin()
                        return

                person = await select_player(message.author, argument, game.seatingOrder)
                if person == None:
                    return

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

                    if vote.order[vote.position].user != person.user:
                        await message.author.send('It\'s not their vote right now. Do you mean @presetvote?')
                        return

                    vt = int(argument == 'yes' or argument == 'y')

                    await vote.vote(vt, operator=message.author)
                    if game != None:
                        backup('current_game.pckl')
                    return

                if vote.order[vote.position].user != (await get_player(message.author)).user:
                    await message.author.send('It\'s not your vote right now. Do you mean @presetvote?')
                    return

                vt = int(argument == 'yes' or argument == 'y')

                await vote.vote(vt)
                if game != None:
                    backup('current_game.pckl')
                return

            # Presets a vote
            elif command == 'presetvote' or command == 'prevote':

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

            # Set a default vote
            elif command == 'defaultvote':

                preferences = {}
                if os.path.isfile(os.path.dirname(os.getcwd()) + '/preferences.pckl'):
                    with open(os.path.dirname(os.getcwd()) + '/preferences.pckl', 'rb') as file:
                        preferences = dill.load(file)

                if argument == '':
                    try:
                        del preferences[message.author.id]['defaultvote']
                        await message.author.send('Removed your default vote.')
                        with open(os.path.dirname(os.getcwd()) + '/preferences.pckl', 'wb') as file:
                            dill.dump(preferences, file)
                    except KeyError:
                        await message.author.send('You have no default vote to remove.')
                    return

                else:
                    argument = argument.split(' ')
                    if len(argument) > 2:
                        await message.author.send('setdefault takes at most two arguments: @setdefault <vote = no> <time = 3600>')
                        return
                    elif len(argument) == 1:
                        try:
                            time = int(argument[0])*60
                            vt = 0
                        except ValueError:
                            if argument[0] in ['yes', 'y', 'no', 'n']:
                                vt = (argument[0] in ['yes', 'y'])
                                time = 3600
                            else:
                                await message.author.send('{} is not a valid number of minutes or vote.'.format(argument[0]))
                                return
                    else:
                        if argument[0] in ['yes', 'y', 'no', 'n']:
                            vt = (argument[0] in ['yes', 'y'])
                        else:
                            await message.author.send('{} is not a valid vote.'.format(argument[0]))
                            return
                        try:
                            time = int(argument[1])*60
                        except ValueError:
                            await message.author.send('{} is not a valid number of minutes.'.format(argument[1]))

                    try:
                        preferences[message.author.id]['defaultvote'] = (vt, time)
                    except KeyError:
                        preferences[message.author.id] = {'defaultvote': (vt, time)}

                    await message.author.send('Successfully set default {} vote at {} minutes.'.format(['no', 'yes'][vt], str(int(time/60))))
                    with open(os.path.dirname(os.getcwd()) + '/preferences.pckl', 'wb') as file:
                        dill.dump(preferences, file)
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

                person = await select_player(message.author, argument, game.seatingOrder + game.storytellers)
                if person == None:
                    return

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

                person = [x for x in (await get_player(message.author)).messageHistory[-1] if x['from'] != await (await get_player(message.author))]['from']

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

                    argument = argument.split(' ')
                    if len(argument) > 2:
                        await message.author.send('There must be exactly one or two comma-separated inputs.')
                        return

                    if len(argument) == 1:
                        person = await select_player(message.author, argument[0], game.seatingOrder)
                        if person == None:
                            return

                        messageText = '**History for {} (Times in UTC):**\n\n**Day 1:**'.format(person.nick)
                        day = 1
                        for msg in person.messageHistory:
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
                            if messageText != '':
                                await message.author.send(messageText)
                            day += 1
                            messageText = '**Day {}:**'.format(str(day))
                        messageText += '\nFrom: {} | To: {} | Time: {}\n**{}**'.format(msg['from'].nick,msg['to'].nick,msg['time'].strftime("%m/%d, %H:%M:%S"),msg['content'])

                    await message.author.send(messageText)
                    return

                if not await get_player(message.author):
                    await message.author.send('You are not in the game. You have no message history.')
                    return

                person = await select_player(message.author, argument, game.seatingOrder + game.storytellers)
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
                        if messageText != '':
                            await message.author.send(messageText)
                        day += 1
                        messageText = '\n\n**Day {}:**'.format(str(day))
                    messageText += '\nFrom: {} | To: {} | Time: {}\n**{}**'.format(msg['from'].nick,msg['to'].nick,msg['time'].strftime("%m/%d, %H:%M:%S"),msg['content'])

                await message.author.send(messageText)
                return

            # Message search
            elif command == 'search':
                if game == None:
                    await message.author.send('There\'s no game right now.')
                    return

                if gamemasterRole in server.get_member(message.author.id).roles:

                    history = []
                    people = []
                    for person in game.seatingOrder:
                        for msg in person.messageHistory:
                            if not msg['from'] in people and not msg['to'] in people:
                                history.append(msg)
                        people.append(person)

                    history = sorted(history, key=lambda i: i['time'])

                    messageText = '**Messages mentioning {} (Times in UTC):**\n\n**Day 1:**'.format(argument)
                    day = 1
                    for msg in history:
                        if not (argument.lower() in msg['content'].lower()):
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

                messageText = '**Messages mentioning {} (Times in UTC):**\n\n**Day 1:**'.format(argument)
                day = 1
                for msg in (await get_player(message.author)).messageHistory:
                    if not (argument.lower() in msg['content'].lower()):
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

            # Create custom alias
            elif command == 'makealias':

                argument = argument.split(' ')
                if len(argument) != 2:
                    await message.author.send('makealias takes exactly two arguments: @makealias <alias> <command>')
                    return

                preferences = {}
                if os.path.isfile(os.path.dirname(os.getcwd()) + '/preferences.pckl'):
                    with open(os.path.dirname(os.getcwd()) + '/preferences.pckl', 'rb') as file:
                        preferences = dill.load(file)

                try:
                    preferences[message.author.id]['aliases'][argument[0]] = argument[1]
                except KeyError:
                    try:
                        preferences[message.author.id]['aliases'] = {argument[0]: argument[1]}
                    except KeyError:
                        preferences[message.author.id] = {'aliases': {argument[0]: argument[1]}}

                await message.author.send('Successfully created alias {} for command {}.'.format(argument[0], argument[1]))
                with open(os.path.dirname(os.getcwd()) + '/preferences.pckl', 'wb') as file:
                    dill.dump(preferences, file)
                return

            # Help dialogue
            elif command == 'help':
                if gamemasterRole in server.get_member(message.author.id).roles:
                    if argument == '':
                        embed = discord.Embed(title='Storyteller Help', description='Welcome to the storyteller help dialogue!')
                        embed.add_field(name='New to storytelling online?', value='Try the tutorial command! (not yet implemented)', inline=False)
                        embed.add_field(name='Formatting commands', value='Prefixes on this server are {}; any multiple arguments are space-separated'.format('\'' + ''.join(list(prefixes)) + '\''))
                        embed.add_field(name='help common', value='Prints commonly used storyteller commands.', inline=False)
                        embed.add_field(name='help progression', value='Prints commands which progress game-time.', inline=False)
                        embed.add_field(name='help day', value='Prints commands related to the day.', inline=False)
                        embed.add_field(name='help gamestate', value='Prints commands which affect the game-state.', inline=False)
                        embed.add_field(name='help info', value='Prints commands which display game information.', inline=False)
                        embed.add_field(name='help player', value='Prints the player help dialogue.', inline=False)
                        embed.add_field(name='help misc', value='Prints miscellaneous commands.', inline=False)
                        embed.add_field(name='Bot Questions?', value='Ask Ben (nihilistkitten#6937)', inline=False)
                        await message.author.send(embed=embed)
                        return
                    elif argument == 'common':
                        embed = discord.Embed(title='Common Commands', description='Multiple arguments are space-separated.')
                        embed.add_field(name='startgame', value='starts the game', inline=False)
                        embed.add_field(name='endgame <<team>>', value='ends the game, with winner team', inline=False)
                        embed.add_field(name='startday <<players>>', value='starts the day, killing players', inline=False)
                        embed.add_field(name='endday', value='ends the day. if there is an execution, execute is preferred', inline=False)
                        embed.add_field(name='kill <<player>>', value='kills player', inline=False)
                        embed.add_field(name='execute <<player>>', value='executes player', inline=False)
                        embed.add_field(name='exile <<traveler>>', value='exiles traveler', inline=False)
                        embed.add_field(name='setdeadline <time>', value='sends a message with time in UTC as the deadline and opens nominations', inline=False)
                        embed.add_field(name='poison <<player>>', value='poisons player', inline=False)
                        embed.add_field(name='unpoison <<player>>', value='unpoisons player', inline=False)
                        await message.author.send(embed=embed)
                        return
                    elif argument == 'player':
                        pass
                    elif argument == 'progression':
                        embed = discord.Embed(title='Game Progression', description='Commands which progress game-time.')
                        embed.add_field(name='startgame', value='starts the game', inline=False)
                        embed.add_field(name='endgame <<team>>', value='ends the game, with winner team', inline=False)
                        embed.add_field(name='startday <<players>>', value='starts the day, killing players', inline=False)
                        embed.add_field(name='endday', value='ends the day. if there is an execution, execute is preferred', inline=False)
                        await message.author.send(embed=embed)
                        return
                    elif argument == 'day':
                        embed = discord.Embed(title='Day-related', description='Commands which affect variables related to the day.')
                        embed.add_field(name='setdeadline <time>', value='sends a message with time in UTC as the deadline and opens nominations', inline=False)
                        embed.add_field(name='openpms', value='opens pms', inline=False)
                        embed.add_field(name='opennoms', value='opens nominations', inline=False)
                        embed.add_field(name='open', value='opens pms and nominations', inline=False)
                        embed.add_field(name='closepms', value='closes pms', inline=False)
                        embed.add_field(name='closenoms', value='closes nominations', inline=False)
                        embed.add_field(name='close', value='closes pms and nominations', inline=False)
                        embed.add_field(name='vote', value='votes for the current player', inline=False)
                        await message.author.send(embed=embed)
                        return
                    elif argument == 'gamestate':
                        embed = discord.Embed(title='Game-State', description='Commands which directly affect the game-state.')
                        embed.add_field(name='kill <<player>>', value='kills player', inline=False)
                        embed.add_field(name='execute <<player>>', value='executes player', inline=False)
                        embed.add_field(name='exile <<traveler>>', value='exiles traveler', inline=False)
                        embed.add_field(name='revive <<player>>', value='revives player', inline=False)
                        embed.add_field(name='changerole <<player>>', value='changes player\'s role', inline=False)
                        embed.add_field(name='changealignment <<player>>', value='changes player\'s alignment', inline=False)
                        embed.add_field(name='changeability <<player>>', value='changes player\'s ability, if applicable to their character (ex apprentice)', inline=False)
                        embed.add_field(name='givedeadvote <<player>>', value='adds a dead vote for player', inline=False)
                        embed.add_field(name='removedeadvote <<player>>', value='removes a dead vote from player. not necessary for ordinary usage', inline=False)
                        embed.add_field(name='poison <<player>>', value='poisons player', inline=False)
                        embed.add_field(name='unpoison <<player>>', value='unpoisons player', inline=False)
                        await message.author.send(embed=embed)
                        return
                    elif argument == 'info':
                        embed = discord.Embed(title='Informative', description='Commands which display information about the game.')
                        embed.add_field(name='history <<player1>> <<player2>>', value='views the message history between player1 and player2', inline=False)
                        embed.add_field(name='history <<player>>', value='views all of player\'s messages', inline=False)
                        embed.add_field(name='search <<content>>', value='views all messages containing content', inline=False)
                        embed.add_field(name='info <<player>>', value='views game information about player', inline=False)
                        embed.add_field(name='grimoire', value='views the grimoire', inline=False)
                        await message.author.send(embed=embed)
                        return
                    elif argument == 'misc':
                        embed = discord.Embed(title='Miscellaneous', description='Commands with miscellaneous uses, primarily for troubleshooting and seating.')
                        embed.add_field(name='makeinactive <<player>>', value='marks player as inactive. must be done in all games player is participating in', inline=False)
                        embed.add_field(name='undoinactive <<player>>', value='undoes an inactivity mark. must be done in all games player is participating in', inline=False)
                        embed.add_field(name='addtraveler <<player>> or addtraveller <<player>>', value='adds player as a traveler', inline=False)
                        embed.add_field(name='removetraveler <<traveler>> or removetraveller <<traveler>>', value='removes traveler from the game', inline=False)
                        embed.add_field(name='cancelnomination', value='cancels the previous nomination', inline=False)
                        embed.add_field(name='reseat', value='reseats the game', inline=False)
                        await message.author.send(embed=embed)
                        return
                embed = discord.Embed(title='Player Commands', description='Multiple arguments are space-separated.')
                embed.add_field(name='New to playing online?', value='Try the tutorial command! (not yet implemented)', inline=False)
                embed.add_field(name='Formatting commands', value='Prefixes on this server are {}; any multiple arguments are space-separated'.format('\'' + ''.join(list(prefixes)) + '\''))
                embed.add_field(name='pm <<player>> or message <<player>>', value='sends player a message', inline=False)
                embed.add_field(name='reply', value='messages the author of the previously received message', inline=False)
                embed.add_field(name='history <<player>>', value='views your message history with player', inline=False)
                embed.add_field(name='search <<content>>', value='views all of your messages containing content', inline=False)
                embed.add_field(name='vote <<yes/no>>', value='votes on an ongoing nomination', inline=False)
                embed.add_field(name='nominate <<player>>', value='nominates player', inline=False)
                embed.add_field(name='presetvote <<yes/no>> or prevote <<yes/no>>', value='submits a preset vote. will not work if it is your turn to vote. not reccomended -- contact the storytellers instead', inline=False)
                embed.add_field(name='cancelpreset', value='cancels an existing preset', inline=False)
                embed.add_field(name='defaultvote <<vote = \'no\'>> <<time=60>>', value='will always vote vote in time minutes. if no arguments given, deletes existing defaults.', inline=False)
                embed.add_field(name='makealias <<alias>> <<command>>', value='creats an alias for a command', inline=False)
                embed.add_field(name='clear', value='returns whitespace', inline=False)
                embed.add_field(name='notactive', value='lists players who are yet to speak', inline=False)
                embed.add_field(name='cannominate', value='lists players who are yet to nominate or skip', inline=False)
                embed.add_field(name='canbenominated', value='lists players who are yet to be nominated', inline=False)
                embed.add_field(name='Bot Questions?', value='Ask Ben (nihilistkitten#6937)', inline=False)
                await message.author.send(embed = embed)
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

            if not (await get_player(after.author)).canNominate:
                await channel.send('You have already nominated.')
                await after.unpin()
                return

            if game.script.isAtheist:
                if argument == 'storytellers' or argument == 'the storytellers' or (len(await generate_possibilities(argument, server.members)) == 1 and gamemasterRole in server.get_member((await generate_possibilities(argument, server.members))[0].id).roles):
                    if None in [x.nominee for x in game.days[-1].votes]:
                        await channel.send('The storytellers have already been nominated today.')
                        await after.unpin()
                        return
                    await game.days[-1].nomination(None, await get_player(after.author))
                    if game != None:
                        backup('current_game.pckl')
                    await after.unpin()
                    return

            names = await generate_possibilities(argument, game.seatingOrder)

            if len(names) == 1:

                if not names[0].canBeNominated:
                    await channel.send('{} has already been nominated.'.format(names[0].nick))
                    await after.unpin()
                    return

                await game.days[-1].nomination(names[0], await get_player(after.author))
                if game != None:
                    backup('current_game.pckl')
                await after.unpin()
                return

            elif len(names) > 1:

                await channel.send('There are too many matching players.')
                await after.unpin()
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

            canNominate = [player for player in game.seatingOrder if player.canNominate == True and player.hasSkipped == False and player.alignment != 'neutral']
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

    if after == client.user:
        return

    if game != None:
        if await get_player(after):
            if before.nick != after.nick:
                (await get_player(after)).nick = after.nick
                await after.send('Your nickname has been updated.')
                backup('current_game.pckl')

        if gamemasterRole in after.roles and not gamemasterRole in before.roles:
            game.storytellers.append(Player(Storyteller, 'neutral', after))
        elif gamemasterRole in before.roles and not gamemasterRole in after.roles:
            for st in game.storytellers:
                if st.user.id == after.id:
                    game.storytellers.remove(st)


### Event loop
while True:
    try:
        client.run(TOKEN)
        print('end')
        time.sleep(5)
    except Exception as e:
        print(str(e))
