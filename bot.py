### fix @nominate permissions qne qee pin argument
import discord, os, time

from config import *


### Global Variables
global isPmsOpen # bool - are pms open
global isNomsOpen # bool - are nominations open
global isDay # bool - is it the day
global notActive # list - players who have not spoken today
global canNominate # list - players who can nominate today
global canBeNominated # list - players who can be nominated today
isPmsOpen = False
isNomsOpen = False
isDay = False
notActive = []
canNominate = []
canBeNominated = []


### API Stuff
client = discord.Client() # discord client

# Read API Token
with open(os.path.dirname(os.path.realpath(__file__))+'/token.txt') as tokenfile:
    TOKEN = tokenfile.readline().strip()


### Utility Functions
async def generate_possibilities(text, people):
    # Generates possible users with name or nickname matching text

    possibilities = []
    for i in people:
        if ((i.nick != None and choice.content.lower() in i.nick.lower()) or choice.content.lower() in i.name.lower()) and playerrole in [g.name for g in i.roles]:
            possibilities.append(i)
    return possibilities

async def is_gamemaster(user):
    # Checks if user has gammasterrole
    return gamemasterrole in [g.name for g in bggserver.get_member(user.id).roles]

async def is_player(user):
    # Checks if user has playerrole
    return playerrole in [g.name for g in bggserver.get_member(user.id).roles]

async def make_active(user):
    # Removes user from notActive

    notActive.remove(user)
    if len(notActive) == 1:
        for memb in bggserver.members:
            if gamemasterrole in [role.name for role in memb.roles]:
                await client.send_message(memb, 'Just waiting on {} to speak.'.format(str(notActive[0])))
    if len(notActive) == 0:
        for memb in bggserver.members:
            if gamemasterrole in [role.name for role in memb.roles]:
                await client.send_message(memb, 'Everyone has spoken!')
    return

async def update_presence(client):
    # Updates Discord Presence

    clopen = ['Closed','Open']
    await client.change_presence(game = discord.Game(name = 'PMs {}, Nominations {}!'.format(clopen[isPmsOpen],clopen[isNomsOpen])))

async def choices(possibilities, user, origin = ''):
    # Clarifies which user is indended when there are multiple matches

    # Generate clarification message
    messageText = 'Which user do you mean to {}?\n'.format(origin)
    for index,u in enumerate(possibilities):
        messageText += '({0}). {1}\n'.format(index+1,u.nick if u.nick else u.name)

    # Request clarifciation from user
    await client.send_message(user,messageText)
    choice = await client.wait_for_message(timeout=200, author=user, channel=pickone.channel)

    # Timeout
    if choice == None:
        await client.send_message(user,'Timed out.')
        return

    # Cancel
    if choice.content.lower() == 'cancel':
        await client.send_message(user,'{} cancelled!'.format(origin))
        return

    # Restart
    if choice.content.lower()[1:].startswith(origin):
        return

    # If a is an int
    try:
        a = possibilities[int(choice.content)-1]
        return possibilities[int(choice.content)-1]

    # If a is a name
    except Exception:
        new_possibilities = generate_possibilities(choice.content, possibilities)

        if len(new_possibilities) == 0:
            await client.send_message(user,'User not found. Try again.')
            return await choices(possibilities,user,message)

        elif len(temp) == 1:
            return new_possibilities[0]

        else:
            return await choices(new_possibilities,user,message)

async def yes_no(user, text):
        await client.send_message(user,'{}? yes or no'.format(text))
        choice = await client.wait_for_message(timeout=200, author=user, channel=pickone.channel)

        # Timeout
        if choice == None:
            await client.send_message(user,'Timed out.')
            return

        # Cancel
        if choice.content.lower() == 'cancel':
            await client.send_message(user,'Action cancelled!')
            return

        # Yes
        if choice.content.lower() == 'yes':
            return True

        # No
        elif choice.content.lower() == 'no':
            return False

        else:
            return client.send_message(user,'Your answer must be \'yes\' or \'no\' exactly. Try again.')
            return await yes_no(user, text)


### Commands

async def open_pms(user):
    # Opens pms

    # Check if pms are already open
    if isPmsOpen:
        await client.send_message(user, 'PMs are already open.')
        return

    isPmsOpen = True # open pms
    await update_presence(client) # update presence
    for user in bggserver.members: # send gamemasters update
        if is_gamemaster(user):
            await client.send_message(user, 'PMs are now open.')
    return

async def open_noms(user):
    # Opens nominations

    # Check if nominations are already open
    if isNomsOpen:
        await client.send_message(user, 'Nominations are already open.')
        return

    isNomsOpen = True # open noms
    await update_presence(client) # update presence
    for user in bggserver.members: # send gamemasters update
        if is_gamemaster(user):
            await client.send_message(user, 'Nominations are now open.')
    return

async def close_pms(user):
    # Closes pms

    # Check if pms are already closed
    if not isPmsOpen:
        await client.send_message(user, 'PMs are already closed.')
        return

    isPmsOpen = False # close pms
    await update_presence(client) # update presence
    for user in bggserver.members: # send gamemasters update
        if is_gamemaster(user):
            await client.send_message(user, 'PMs are now closed.')
    return

async def close_noms(user):
    # Closes nominations

    # Check if nominations are already closed
    if not isNomsOpen:
        await client.send_message(user, 'Nominations are already closed.')
        return

    isNomsOpen = False # close noms
    await update_presence(client) # update presence
    for user in bggserver.members:
        if is_gamemaster(user):
            await client.send_message(user, 'Nominations are now closed.')
    return

async def start_day(user, argument):
    # Starts the day

    # Check if it is already day
    if isDay:
        await client.send_message(user, 'It is already day.')
        return

    # Deaths
    await client.send_message(user, 'Killing:')
    people = argument.split(', ')
    deaths = []
    players = [player for player in bggserver.members if is_player(player)]
    for player in people:
        possibilities = generate_possibilities(player, players)

        # If no users found
        if len(possiblities) == 0:
            await client.send_message(user, 'User {} not found. Try again!'.format(player))
            return

        # If too many users found
        elif len(possiblities) > 1:
            person = await choices(possibilities, frm, 'message')
            if person == None: # means no choice was selected
                return

        # If exactly one user found
        elif len(possiblities) == 1:
            person = possibilities[0]

        deaths.append(person)
        client.send_message(user, person.nick if person.nick else person.name)

    # Confirm deaths
    confirm = await yes_no(user,'Confirm deaths?')
    if confirm == None or confirm == False:
        return

    for player in deaths:
        kill(user, player.name)

    isDay = True # start the day
    notActive = [player for player in bggserver.members if is_player(player)] # generate notActive
    canBeNominated = notActive # generate canBeNominated
    canNominate = [player for player in notActive if ghostrole not in [g.name for g in bggserver.get_member(nominator.id).roles]] # generate canNominate
    return

    # Announce morning
    role = None
    for rl in bggserver.roles: # find player role
        if rl.name == playerrole:
            role = rl
            break
    announcement = await client.send_message(client.get_channel(publicchannel),"{} wake up!".format(role.mention)) # announcement
    await announcememt.pin() # pin
    return

async def end_day(user):
    # Ends the day

    # Check if it is already night
    if not isDay:
        await client.send_message(user, 'It is already night.')
        return

    isDay = False # end the day

    # Announce night
    role = None
    for rl in bggserver.roles: # find player role
        if rl.name == playerrole:
            role = rl
            break
    announcement = await client.send_message(client.get_channel(publicchannel),"{} go to sleep!".format(role.mention)) # announcement
    await announcement.pin() # pin

async def clear():
    # Creates whitespace in message history

    await client.send_message(message.author,'{}Clearing\n{}'.format('\u200B\n' * 25, '\u200B\n' * 25))
    return

async def not_active(user):
    # Lists inactive users

    # If not day
    if not isDay:
        await client.send_message(user, 'It\'s not day right now!')

    # If no inactive users
    if not notActive:
        await client.send_message(user, 'Everyone has spoken!')
        return

    # Create message
    messageText = 'These players have not spoken:\n'
    for user in notActive:
        messageText += '{}\n'.format(user.nick if user.nick else user.name)

    # Send message
    await client.send_message(user, messageText)

async def can_nominate(user):
    # Lists who can nominate

    # If not day
    if not isDay:
        await client.send_message(user, 'It\'s not day right now!')

    # If noone can nominate
    if not canNominate:
        await client.send_message(user, 'Noone may nominate!')
        return

    # Create message
    messageText = 'These players may nominate:\n'
    for user in canNominate:
        messageText += '{}\n'.format(user.nick if user.nick else user.name)

    # Send message
    await client.send_message(user, messageText)

async def can_be_nominated(user):
    # Lists users who can be nominated

    # If not day
    if not isDay:
        await client.send_message(user, 'It\'s not day right now!')

    # If noone can be nominated
    if not canBeNominated:
        await client.send_message(user, 'Everyone has been nominated!')
        return

    # Create message
    messageText = 'These players may be nominated:\n'
    for user in canBeNominated:
        messageText += '{}\n'.format(user.nick if user.nick else user.name)

        # Send message
    await client.send_message(user, messageText)

async def pm(to, frm):
    # Sends a pm

    # Possible matches
    players = [player for player in bggserver.members if is_player(player)]
    possibilities = generate_possibilities(to,players)

    # If no users found
    if len(possiblities) == 0:
        await client.send_message(frm, 'User not found. Try again!')
        return

    # If too many users found
    elif len(possiblities) > 1:
        person = await choices(possibilities, frm, 'message')
        if person == None: # means no choice was selected
            return

    # If exactly one user found
    elif len(possiblities) == 1:
        person = possibilities[0]

    # Request content
    messageText = 'Messaging {}. What would you like to send?'.format(person.nick if person.nick else person.name)
    await client.send_message(frm,messageText)

    # Process reply
    intendedMessage = await client.wait_for_message(timeout=200, author=frm, channel=reply.channel)

    # Timeout
    if intendedMessage == None:
        await client.send_message(frm, 'Message timed out!')
        return

    # Cancel
    if intendedMessage.content.lower() == 'cancel':
        await client.send_message(frm, 'Message canceled!')
        return

    # Restart
    if intendedMessage.content.lower()[1:].startswith('message'):
        return

    # Send message
    await client.send_message(person, 'Message from {}: **{}**'.format(bggserver.get_member(frm.id).nick if bggserver.get_member(frm.id).nick else frm.name, intendedMessage.content))

    # Inform gamemasters
    for user in bggserver.members:
        if is_gamemaster(user) and user != frm and user != person:
                await client.send_message(member, '**[**{} **>** {}**]** {}'.format(server.get_member(frm.id).nick if server.get_member(frm.id).nick else frm.name, person.nick if person.nick else person.name,intendedMessage.content))

    # Announce message
    await client.send_message(client.get_channel(publicchannel), '**{}** > **{}**'.format(server.get_member(frm.id).nick if server.get_member(frm.id).nick else frm.name, person.nick if person.nick else person.name))

    # Update activity
    if user in notActive:
        make_active(frm)

    # Confirm success
    await client.send_message(frm, 'Message sent!')
    return

async def nominate(nominator, argument, pin=False, location=None):
    # nominates a player found in argument

    # Generate location
    if location == None:
        location = nominator # will send response messages in dm

    # Check if nominations are open
    if not nomsopen and not is_gamemaster(nominator):
        await client.send_message(client.get_channel(publicchannel), 'Nominations are closed.')
        await client.unpin_message(after)
        return

    # Check if nominator is a player
    elif not is_player(nominator):
        await client.send_message(location, '{}, you are not in the game and do not have permission to nominate.'.format(nominator.mention))
        await client.unpin_message(after)
        return

    # Determine nominee
    # Self-nomination
    if 'me' in argument or 'myself' in argument:
        nominee = after.author

    # Storyteller nomination
    elif 'storyteller' in argument:
        role = None
        for rl in bggserver.roles:
            if rl.name == gamemasterrole:
                role = rl
                break
        nominee = role

    # Other nominations
    else:
        players = [player for player in bggserver.members if is_player(player)]
        names = generate_possibilities(argument, players)
        if len(name) > 1:
            await client.send_message(location, '{}, there are multiple matching players: {}. Please try again.'.format(nominator.mention, names))
            return
        elif len(name) == 0:
            await client.send_message(location, '{}. there are no matching players. Please try again.'.format(nominator.mention))
            return
        else:
            nominee = names[0]

    # Check if nominator is dead
    if ghostrole in [g.name for g in bggserver.get_member(nominator.id).roles] and travelerrole not in [g.name for g in bggserver.get_member(nominee.id).roles]:
        await client.send_message(location, '{}, you are dead and cannot nominate.'.format(nominator.mention))
        await client.unpin_message(after)
        return

    # Check if nominator has nominated today
    elif nominator not in canNominate and travelerrole not in [g.name for g in bggserver.get_member(nominee.id).roles]:
        await client.send_message(location, '{}, you have nominated already today.'.format(nominator.mention))
        await client.unpin_message(after)
        return

    # Check if nominee has been nominated today
    elif nominee not in canBeNominated:
        await client.send_message(location, '{}, {} has already been nominated today.'.format(nominator.menion, nominee.mention))
        await client.unpin_message(after)

    # Nomination
    if not travelerrole not in [g.name for g in bggserver.get_member(nominee.id).roles]: # update canNominate
        canNominate.remove(nominator)
    canbeNominated.remove(moninee) # update canBeNominated
    isPmsOpen == False # update pms
    isNomsOpen == False # update noms
    await update_presence(client) # update presence
    announcement = await client.send_message(client.get_channel(publicchannel), '{} has been nominated by {}.'.format(nominee.mention, nominator.mention)) # send announcement

    # Pin
    if pin:
        await announcement.pin()

    return

async def kill(user, argument):
    # Kills a player

    # Possible matches
    players = [player for player in bggserver.members if is_player(player)]
    possibilities = generate_possibilities(argument,players)

    # If no users found
    if len(possiblities) == 0:
        await client.send_message(user, 'User not found. Try again!')
        return

    # If too many users found
    elif len(possiblities) > 1:
        person = await choices(possibilities, user, 'kill')
        if person == None: # means no choice was selected
            return

    # If exactly one user found
    elif len(possiblities) == 1:
        person = possibilities[0]

    # Check if dead
    if ghostrole in [g.name for g in bggserver.get_member(nominator.id).roles]:
        await client.send_message(user, '{} is already dead.'.format(person.nick if person.nick else person.name))
        return

    # Find dead role
    role = None
    for rl in bggserver.roles:
        if rl.name == ghostrole:
            role = rl
            break

    # Find dead vote role
    role2 = None
    for rl in bggserver.roles:
        if rl.name == deadvoterole:
            role = rl
            break

    # Add roles
    person.add_roles(role, role2)

    # Announce death
    announcement = await client.send_message(client.get_channel(publicchannel), '{} has died.'.format(person.nick if person.nick else person.name)) # announcement
    await announcement.pin() # pin

async def execute(user, argument):
    # Executes a player

    # Possible matches
    players = [player for player in bggserver.members if is_player(player)]
    possibilities = generate_possibilities(argument,players)

    # If no users found
    if len(possiblities) == 0:
        await client.send_message(user, 'User not found. Try again!')
        return

    # If too many users found
    elif len(possiblities) > 1:
        person = await choices(possibilities, user, 'execute')
        if person == None: # means no choice was selected
            return

    # If exactly one user found
    elif len(possiblities) == 1:
        person = possibilities[0]

    # Check if person dies
    death = await yes_no(user,'Does {} die?'.format(person.nick if person.nick else person.name))
    if death == None:
        return

    # Check if day ends
    day_end = await yes_no(user,'Does the day end?')
    if day_end == None:
        return

    # Announce execution
    announcement = await client.send_message(client.get_channel(publicchannel), '{} has been executed.'.format(person.nick if person.nick else person.name)) # announcement
    await announcement.pin() # pin

    # Resolve death
    if death:
        await kill(user, person.name)

    # Resolve day end
    if day_end:
        await end_day(user)

async def exile(user, argument):
    # Exiles a player

    # Possible matches
    players = [player for player in bggserver.members if is_player(player)]
    possibilities = generate_possibilities(argument,players)

    # If no users found
    if len(possiblities) == 0:
        await client.send_message(user, 'User not found. Try again!')
        return

    # If too many users found
    elif len(possiblities) > 1:
        person = await choices(possibilities, user, 'exile')
        if person == None: # means no choice was selected
            return

    # If exactly one user found
    elif len(possiblities) == 1:
        person = possibilities[0]

    # Check is person is traveler
    if travelerrole not in [g.name for g in bggserver.get_member(person.id).roles]:
        await client.send_message(user, '{} is not a traveler.'.format(person.nick if person.nick else person.name))
        return

    # Check if person dies
    death = await yes_no(user,'Does {} die?'.format(person.nick if person.nick else person.name))
    if death == None:
        return

    # Announce exile
    announcement = await client.send_message(client.get_channel(publicchannel), '{} has been executed.'.format(person.nick if person.nick else person.name)) # announcement
    await announcement.pin() # pin

    # Resolve death
    if death:
        await kill(user, person.name)

async def revive(user, argument):
    # Revives a player

    # Possible matches
    players = [player for player in bggserver.members if is_player(player)]
    possibilities = generate_possibilities(argument,players)

    # If no users found
    if len(possiblities) == 0:
        await client.send_message(user, 'User not found. Try again!')
        return

    # If too many users found
    elif len(possiblities) > 1:
        person = await choices(possibilities, user, 'revive')
        if person == None: # means no choice was selected
            return

    # If exactly one user found
    elif len(possiblities) == 1:
        person = possibilities[0]

    # Check if dead
    if ghostrole not in [g.name for g in bggserver.get_member(nominator.id).roles]:
        await client.send_message(user, '{} is already alive.'.format(person.nick if person.nick else person.name))
        return

    # Find dead role
    role = None
    for rl in bggserver.roles:
        if rl.name == ghostrole:
            role = rl
            break

    # Find dead vote role
    role2 = None
    for rl in bggserver.roles:
        if rl.name == deadvoterole:
            role = rl
            break

    # Remove roles
    person.remove_roles(role, role2)

    # Announce ressurection
    announcement = await client.send_message(client.get_channel(publicchannel), '{} has come back to life.'.format(person.nick if person.nick else person.name)) # announcement
    await announcement.pin() # pin


### Event Handling
@client.event
async def on_ready():
    # On login

    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await update_presence(client)

@client.event
async def on_message(message):
    # Handles messages on reception
    global isPmsOpen
    global isNomsOpen
    global isDay
    global notActive
    global canNominate
    global canBeNominated
    global bggserver
    bggserver = client.get_server(bggid)

    # Don't respond to self
    if message.author == client.user:
        return

    # Public Channel
    if message.channel.id == publicchannel:

        # Update activity
        if (message.author in notActive) and isDay:
            make_active(message.author)
        return

    # Check if not dm
    if message.server != None:
        return

    # Check if command
    elif message.content.startswith(',') or message.content.startswith('@'):

        # Generate command and arguments
        command = message.content[1:message.content.index(' ')]
        arguments = message.content[message.content.index(' ') + 1:]

        # Opens pms
        if command == 'openpms':
            if not is_gamemaster(message.author): # check permissions
                await client.send_message(message.author, 'You don\'t have permission to open PMs.')
                return
            await open_pms(message.author)
            return

        # Opens nominations
        elif command == 'opennoms':
            if not is_gamemaster(message.author): # check permissions
                await client.send_message(message.author, 'You don\'t have permission to open nominations.')
                return
            await open_noms(message.author)
            return

        # Opens pms and nominations
        elif command == 'open':
            if not is_gamemaster(message.author): # check permissions
                await client.send_message(message.author, 'You don\'t have permission to open PMs and nominations.')
                return
            await open_pms(message.author)
            await open_noms(message.author)
            return

        # Closes pms
        elif command == 'closepms':
            if not is_gamemaster(message.author): #check permissions
                await client.send_message(message.author, 'You don\'t have permission to close PMs.')
                return
            await close_pms(message.author)
            return

        # Closes nominations
        elif command == 'closenoms':
            if not is_gamemaster(message.author): # check permissions
                await client.send_message(message.author, 'You don\'t have permission to close nominations.')
                return
            await close_noms(message.author)
            return

        # Closes pms and nominations
        elif command == 'close':
            if not is_gamemaster(message.author): # check permissions
                await client.send_message(message.author, 'You don\'t have permission to close PMs and nominations.')
                return
            await close_pms(message.author)
            await close_noms(message.author)
            return

        # Starts day
        elif command == 'startday':
            if not is_gamemaster(message.author): # check permissions
                await client.send_message(message.author, 'You don\'t have permission to start the day.')
                return
            await open_pms(message.author)
            await start_day(message.author, argument)
            return

        # Ends day
        elif command == 'endday':
            if not is_gamemaster(message.author): # check permissions
                await client.send_message(message.author, 'You don\'t have permission to end the day.')
                return
            await close_pms(message.author)
            await close_noms(message.author)
            await end_day(message.author)
            return

        # Kills a player
        elif command == 'kill':
            if not is_gamemaster(message.author): # check permissions
                await client.send_message(message.author, 'You don\'t have permission to kill players.')
                return
            await kill(message.author, argument)
            return

        # Executes a player
        elif command == 'execute':
            if not is_gamemaster(message.author): # check permissions
                await client.send_message(message.author, 'You don\'t have permission to execute players.')
                return
            await execute(message.author, argument)
            return

        # Exiles a traveler
        elif command == 'exile':
            if not is_gamemaster(message.author): # check permissions
                await client.send_message(message.author, 'You don\'t have permission to exile travelers.')
                return
            await exile(message.author, argument)
            return

        # Revives a player
        elif command == 'revive':
            if not is_gamemaster(message.author): # check permissions
                await client.send_message(message.author, 'You don\'t have permission to revive players.')
                return
            await revive(message.author, argument)
            return

        # Nominates
        elif command == 'nominate':
            if not is_gamemaster(message.author): # check permissions
                await client.send_message(message.author, 'You don\'t have permission to use @nominate.')
                return
            await nominate(message.author, argument)
            return

        # Clears history
        elif command == 'clear':
            await clear(message.author)
            return

        # Checks active players
        elif command == 'notactive':
            await not_active(message.author)
            return

        # Checks who can nominate
        elif command == 'cannominate':
            await can_nominate(message.author)
            return

        # Checks who can be nominated
        elif command == 'canbenominated':
            await can_be_nominated(message.author)
            return

        # Sends pm
        elif command == 'pm' or command == 'message':
            if not isPmsOpen: # Check if PMs open
                await client.send_message(message.author, 'PMs are closed.')
                return

            if not is_player(message.author): # Check permissions
                await client.send_message(message.author, 'You are not in the game. You may not send messages.')
                return

            await pm(argument,message.author)
            return

        # Help dialogue
        elif command == 'help':
            await client.send_message(message.author, '**Commands:**\nopenpms: Opens pms\nopennoms: Opens noms\nopen: Opens pms and noms\nclosepms: Closes pms\nclosenoms: Closes noms\nclose: Closes pms and noms\nstartday <<players>>: Starts the day, killing players\nendday: Ends the day\nkill <<player>>: Kills player\nexecute <<player>>: Executes player\nexile <<traveler>>: Exiles traveler\nRevive <<player>>: revives player\nnominate <<player>>: Nominates player\n\nclear: Clears previous messages\nnotactive: Lists players yet to speak\ncannominate: Lists who can nominate today\ncanbenominated: Lists who can be nominated today\nmessage <<player>>: Privately messages player\npm <<player>>: Privately messages player\nhelp: Displays this dialogue\n\nCommand keys: @ and ,\nArgument separator: \', \'')
            return

        # Command unrecognized
        else:
            await client.send_message(message.author, 'Command {} not recognized. For a list of commands, type @help.'.format(command))


@client.event
async def on_message_edit(before, after):
    # Handles messages on modification
    global isPmsOpen
    global isNomsOpen
    global isDay
    global notActive
    global canNominate
    global canBeNominated
    global bggserver
    bggserver = client.get_server(bggid)

    # On pin
    if after.channel == client.get_channel(publicchannel) and before.pinned == False and after.pinned == True:

        # Nomination
        if 'nominate ' in after.content.lower(): # -1 to ensure there's something after the nomination

            # Check if nominations are open
            await nominate(after.author, after.content[after.content.lower().index('nominate ') + 1:], client.get_channel(publicchannel))
            return


### Loop
while True:
    client.run(TOKEN)
    print('end')
    time.sleep(5)
