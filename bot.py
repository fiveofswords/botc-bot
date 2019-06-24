import discord, os, time, pickle

from config import *



### API Stuff
client = discord.Client(status="Online") # discord client

# Read API Token
with open(os.path.dirname(os.path.realpath(__file__))+'/token.txt') as tokenfile:
    TOKEN = tokenfile.readline().strip()


### Utility Functions
async def common_name(user):
    # Returns nickname is exists, username otherwise

    if user.nick:
        return user.nick
    return user.name

async def generate_possibilities(text, people):
    # Generates possible users with name or nickname matching text

    possibilities = []
    for i in people:
        if ((i.nick != None and text.lower() in i.nick.lower()) or text.lower() in i.name.lower()):
            possibilities.append(i)
    return possibilities

async def is_role(user, role):
    # Checks if user has role
    return role in [g.name for g in bggserver.get_member(user.id).roles]

async def is_player(user):
    # Checks if user has playerrole
    return await is_role(user, playerrole)

async def is_gamemaster(user):
    # Checks if user has gamemasterrole
    return await is_role(user, gamemasterrole)

async def make_active(user):
    # Removes user from notActive
    global notActive

    notActive.remove(user)
    if len(notActive) == 1:
        for memb in bggserver.members:
            if await is_gamemaster(memb):
                await memb.send('Just waiting on {} to speak.'.format(str(notActive[0])))
    if len(notActive) == 0:
        for memb in bggserver.members:
            if await is_gamemaster(memb):
                await memb.send('Everyone has spoken!')
    return

async def cannot_nominate(user):
    # Removes user from canNominate
    global canNominate

    canNominate.remove(user)
    if len([x for x in canNominate if x not in hasSkipped]) == 1:
        for memb in bggserver.members:
            if await is_gamemaster(memb):
                await memb.send('Just waiting on {} to nominate or skip.'.format(str([x for x in canNominate if x not in hasSkipped][0])))
    if len([x for x in canNominate if x not in hasSkipped]) == 0:
        for memb in bggserver.members:
            if await is_gamemaster(memb):
                await memb.send('Everyone has nominated or skipped!')
    return

async def update_presence(client):
    # Updates Discord Presence

    clopen = ['Closed','Open']
    await client.change_presence(status=discord.Status.idle, activity = discord.Game(name = 'PMs {}, Nominations {}!'.format(clopen[isPmsOpen],clopen[isNomsOpen])))

async def choices(possibilities, user, origin = ''):
    # Clarifies which user is indended when there are multiple matches

    # Generate clarification message
    messageText = 'Which user do you mean to {}?\n'.format(origin)
    for index,u in enumerate(possibilities):
        messageText += '({0}). {1}\n'.format(index+1,u.nick if u.nick else u.name)

    # Request clarifciation from user
    reply = await user.send(messageText)
    choice = await client.wait_for('message', check=(lambda x: x.author==user and x.channel==reply.channel), timeout=200)

    # Timeout
    if choice == None:
        await user.send('Timed out.')
        return

    # Cancel
    if choice.content.lower() == 'cancel':
        await user.send('{} cancelled!'.format(origin))
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
        new_possibilities = await generate_possibilities(choice.content, possibilities)

        if len(new_possibilities) == 0:
            await user.send('User not found. Try again.')
            return await choices(possibilities,user,origin)

        elif len(new_possibilities) == 1:
            return new_possibilities[0]

        else:
            return await choices(new_possibilities,user,origin)

async def yes_no(user, text):
    # Ask a yes or no question of a user

    reply = await user.send('{}? yes or no'.format(text))
    choice = await client.wait_for('message', check=(lambda x: x.author==user and x.channel==reply.channel), timeout=200)

    # Timeout
    if choice == None:
        await user.send('Timed out.')
        return

    # Cancel
    if choice.content.lower() == 'cancel':
        await user.send('Action cancelled!')
        return

    # Yes
    if choice.content.lower() == 'yes':
        return True

    # No
    elif choice.content.lower() == 'no':
        return False

    else:
        return user.send('Your answer must be \'yes\' or \'no\' exactly. Try again.')
        return await yes_no(user, text)

async def select_player(user, text, players, origin = ''):
    # Finds a player from players matching a string

    possibilities = await generate_possibilities(text, players)

    # If no users found
    if len(possibilities) == 0:
        await user.send('User {} not found. Try again!'.format(text))
        return

    # If too many users found
    elif len(possibilities) > 1:
        person = await choices(possibilities, user, origin)
        if person == None: # means no choice was selected
            return

    # If exactly one user found
    elif len(possibilities) == 1:
        person = possibilities[0]

    return person

async def store_status():
    global isPmsOpen, isNomsOpen, isDay, isExecutionToday
    file = open("status.pckl","wb")
    pickle.dump((isPmsOpen, isNomsOpen, isDay, isExecutionToday), file)
    file.close()


### Commands
async def open_pms(user):
    # Opens pms
    global isPmsOpen

    # Check if pms are already open
    if isPmsOpen:
        await user.send('PMs are already open.')
        return

    isPmsOpen = True # open pms
    await update_presence(client) # update presence
    await store_status()
    for user in bggserver.members: # send gamemasters update
        if await is_gamemaster(user):
            await user.send('PMs are now open.')
    return

async def open_noms(user):
    # Opens nominations
    global isNomsOpen

    # Check if nominations are already open
    if isNomsOpen:
        await user.send('Nominations are already open.')
        return

    isNomsOpen = True # open noms
    await update_presence(client) # update presence
    await store_status()
    for user in bggserver.members: # send gamemasters update
        if await is_gamemaster(user):
            await user.send('Nominations are now open.')
    return

async def close_pms(user):
    # Closes pms
    global isPmsOpen

    # Check if pms are already closed
    if not isPmsOpen:
        await user.send('PMs are already closed.')
        return

    isPmsOpen = False # close pms
    await update_presence(client) # update presence
    await store_status()
    for user in bggserver.members: # send gamemasters update
        if await is_gamemaster(user):
            await user.send('PMs are now closed.')
    return

async def close_noms(user):
    # Closes nominations
    global isNomsOpen

    # Check if nominations are already closed
    if not isNomsOpen:
        await user.send('Nominations are already closed.')
        return

    isNomsOpen = False # close noms
    await update_presence(client) # update presence
    await store_status()
    for user in bggserver.members:
        if await is_gamemaster(user):
            await user.send('Nominations are now closed.')
    return

async def start_day(user, argument):
    # Starts the day
    global isDay
    global isExecutionToday
    global notActive
    global canBeNominated
    global canNominate
    global hasSkipped

    if not argument == '':
        if not await kill(user, argument):
            return
    else:
        await client.get_channel(publicchannel).send('No one has died.')

    # Check if it is already day
    if isDay:
        await user.send('It is already day.')
        return

    # Open pms
    await open_pms(user)

    isDay = True # start the day
    isExecutionToday = False # reset execution counter
    await store_status()
    notActive = [player for player in bggserver.members if (await is_player(player) and not await is_role(player, inactiverole) and not await is_gamemaster(player))] # generate notActive
    canBeNominated = [player for player in bggserver.members if (await is_player(player) and not await is_role(player, inactiverole) and not await is_gamemaster(player))] # generate canBeNominated
    canNominate = [player for player in bggserver.members if (not await is_role(player, ghostrole) and await is_player(player) and not await is_role(player, inactiverole) and not await is_gamemaster(player))] # generate canNominate
    hasSkipped = [] # reset hasSkipped

    # Announce morning
    role = None
    for rl in bggserver.roles: # find player role
        if rl.name == playerrole:
            role = rl
            break
    announcement = await client.get_channel(publicchannel).send('{}, wake up!'.format(role.mention)) # announcement
    return

async def end_day(user):
    # Ends the day
    global isDay
    global isExecutionToday

    print(isExecutionToday)

    # Close pms and nominations
    await close_pms(user)
    await close_noms(user)

    # Check if it is already night
    if not isDay:
        await user.send('It is already night.')
        return

    isDay = False # end the day
    await store_status()
    # Announce no execution
    if not isExecutionToday:
        await client.get_channel(publicchannel).send('No one was executed.')

    # Announce night
    role = None
    for rl in bggserver.roles: # find player role
        if rl.name == playerrole:
            role = rl
            break
    announcement = await client.get_channel(publicchannel).send('{}, go to sleep!'.format(role.mention))

async def clear(user):
    # Creates whitespace in message history

    await user.send('{}Clearing\n{}'.format('\u200B\n' * 25, '\u200B\n' * 25))
    return

async def not_active(user):
    # Lists inactive users
    global isDay
    global notActive

    # If not day
    if not isDay:
        await user.send('It\'s not day right now!')
        return

    # If no inactive users
    if notActive == []:
        await user.send('Everyone has spoken!')
        return

    # Create message
    messageText = 'These players have not spoken:\n'
    for player in notActive:
        messageText += '{}\n'.format(await common_name(player))

    # Send message
    await user.send(messageText)
    return

async def can_nominate(user):
    # Lists who can nominate
    global canNominate
    global isDay

    # If not day
    if not isDay:
        await user.send('It\'s not day right now!')
        return

    # If noone can nominate
    if not ([x for x in canNominate if x not in hasSkipped]):
        await user.send('Everyone has nominated or skipped!')
        return

    # Create message
    messageText = 'These players may still nominate:\n'
    for player in ([x for x in canNominate if x not in hasSkipped]):
        messageText += '{}\n'.format(await common_name(player))

    # Send message
    await user.send(messageText)
    return

async def can_be_nominated(user):
    # Lists users who can be nominated
    global canBeNominated
    global isDay

    # If not day
    if not isDay:
        await user.send('It\'s not day right now!')
        return

    # If noone can be nominated
    if not canBeNominated:
        await user.send('Everyone has been nominated!')
        return

    # Create message
    messageText = 'These players may be nominated:\n'
    for player in canBeNominated:
        messageText += '{}\n'.format(await common_name(player))

        # Send message
    await user.send(messageText)
    return

async def pm(to, frm):
    # Sends a pm
    global isPmsOpen

    # Determine player
    players = [player for player in bggserver.members if await is_player(player)]
    person = await select_player(frm, to, players, origin = 'message')
    if person == None:
        return

    # Request content
    messageText = 'Messaging {}. What would you like to send?'.format(await common_name(person))
    reply = await frm.send(messageText)

    # Process reply
    intendedMessage = await client.wait_for('message', check=(lambda x: x.author==frm and x.channel==reply.channel), timeout=200)

    # Timeout
    if intendedMessage == None:
        await frm.send('Message timed out!')
        return

    # Cancel
    if intendedMessage.content.lower() == 'cancel':
        await frm.send('Message canceled!')
        return

    # Restart
    if intendedMessage.content.lower()[1:].startswith('message'):
        return

    # Send message
    await person.send('Message from {}: **{}**'.format(bggserver.get_member(frm.id).nick if bggserver.get_member(frm.id).nick else frm.name, intendedMessage.content))

    # Inform gamemasters
    for user in bggserver.members:
        if await is_gamemaster(user) and user != frm and user != person:
            await user.send('**[**{} **>** {}**]** {}'.format(bggserver.get_member(frm.id).nick if bggserver.get_member(frm.id).nick else frm.name, await common_name(person),intendedMessage.content))

    # Announce message
    await client.get_channel(publicchannel).send('**{}** > **{}**'.format(bggserver.get_member(frm.id).nick if bggserver.get_member(frm.id).nick else frm.name, await common_name(person)))

    # Update activity
    if frm in notActive:
        await make_active(frm)

    # Confirm success
    await frm.send('Message sent!')
    return

async def nominate(nominator, argument, message=None, location=None, pin=False):
    # nominates a player found in argument
    global canNominate
    global canBeNominated
    global isDay

    # Check if day
    if not isDay:
        await location.send('{}, it\'s not the day right now. Try again later.'.format(nominator.mention))

    # Generate location
    if location == None:
        location = nominator # will send response messages in dm

    # Check if nominations are open
    if not isNomsOpen and not await is_gamemaster(nominator):
        await client.get_channel(publicchannel).send('Nominations are closed.')
        await message.unpin()
        return

    # Check if nominator is a player
    elif not await is_player(nominator):
        await location.send('{}, you are not in the game and do not have permission to nominate.'.format(nominator.mention))
        await message.unpin()
        return

    # Determine nominee
    # Self-nomination
    if argument == 'me' or argument == 'myself':
        nominee = nominator

    # Storyteller nomination
    #elif 'storyteller' in argument:
    #    role = None
    #    for rl in bggserver.roles:
    #        if rl.name == gamemasterrole:
    #            role = rl
    #            break
    #    nominee = role

    # Other nominations
    else:
        players = [player for player in bggserver.members if await is_player(player)]
        names = await generate_possibilities(argument, players)
        if len(names) > 1:
            await location.send('{}, there are multiple matching players. Please try again.'.format(nominator.mention))
            await message.unpin()
            return
        elif len(names) == 0:
            await location.send('{}. there are no matching players. Please try again.'.format(nominator.mention))
            await message.unpin()
            return
        else:
            nominee = names[0]

    print(nominee)
    print(nominator)
    print(canBeNominated)
    print(canNominate)
    # Check if nominator is dead
    if await is_role(nominator, ghostrole) and not await is_role(nominee, travelerrole):
        await location.send('{}, you are dead and cannot nominate.'.format(nominator.mention))
        await message.unpin()
        return

    # Check if nominator has nominated today
    elif nominator not in canNominate and not await is_role(nominee, travelerrole) and not await is_gamemaster(nominator):
        await location.send('{}, you have nominated already today.'.format(nominator.mention))
        await message.unpin()
        return

    # Check if nominee has been nominated today
    elif nominee not in canBeNominated:
        await location.send('{}, {} has already been nominated today.'.format(nominator.mention, await common_name(nominee)))
        await message.unpin()
        return

    # Nomination
    if not await is_role(nominee, travelerrole) and not await is_gamemaster(nominator): # update canNominate
       await cannot_nominate(nominator)
    canBeNominated.remove(nominee) # update canBeNominated
    isPmsOpen == False # update pms
    isNomsOpen == False # update noms
    await update_presence(client) # update presence
    await store_status()

    # Announcement for exile call
    if await is_role(nominee, travelerrole):
        announcement = await client.get_channel(publicchannel).send('{} has called for {}\'s exile'.format(nominator.mention, nominee.mention)) # send announcement

    # Announcement for nomination
    else:
        announcement = await client.get_channel(publicchannel).send('{} has been nominated by {}.'.format(nominee.mention, nominator.mention)) # send announcement

    # Pin
    if pin:
        await announcement.pin()

    return

async def kill(user, argument, suppress=False):
    # Kills a player

    # Argument Handling
    people = argument.split(', ')

    # If deaths
    await user.send('Killing:')
    deaths = []
    players = [player for player in bggserver.members if await is_player(player)]
    for player in people:
        person = await select_player(user, player, players, origin = 'kill')
        if person == None:
            return
        deaths.append(person)
        await user.send(await common_name(person))

    # Confirm deaths
    if not suppress:
        confirm = await yes_no(user,'Confirm deaths')
        if confirm == None or confirm == False:
            return

    for person in deaths:

    # Determine player
        # Check if dead
        if await is_role(person, ghostrole):
            await user.send('{} is already dead.'.format(await common_name(person)))
            return

        # Find ghost role
        role = None
        for rl in bggserver.roles:
            if rl.name == ghostrole:
                role = rl
                break

        # Find dead vote role
        role2 = None
        for rl in bggserver.roles:
            if rl.name == deadvoterole:
                role2 = rl
                break

        # Add roles
        await person.add_roles(role)
        await person.add_roles(role2)

    # Announce deaths
    if not suppress:
        if len(deaths) == 1:
            announcement = await client.get_channel(publicchannel).send('{} has died.'.format(await common_name(deaths[0]))) # announcement
            await announcement.pin()
        elif len(deaths) == 2:
            announcement = await client.get_channel(publicchannel).send('{} and {} have died.'.format(await common_name(deaths[0]), await common_name(deaths[1]))) # announcement
        else:
            string = ', '.join([await common_name(person) for person in deaths[:-1]]) + ', and ' + await common_name(deaths[-1])
            announcement = await client.get_channel(publicchannel).send('{} have died.'.format(string)) # announcement
            await announcement.pin() # pin

    return True

async def execute(user, argument):
    # Executes a player
    global isExecutionToday

    # Determine player
    players = [player for player in bggserver.members if await is_player(player)]
    person = await select_player(user, argument, players, origin = 'execute')
    if person == None:
        return

    # Check if person dies
    death = await yes_no(user,'Does {} die'.format(await common_name(person)))
    if death == None:
        return

    # Check if day ends
    day_end = await yes_no(user,'Does the day end')
    if day_end == None:
        return

    # Announce execution
    if death:
        announcement = await client.get_channel(publicchannel).send('{} has been executed.'.format(await common_name(person))) # announcement
        await announcement.pin() # pin
        await kill(user, person.name, suppress=True)
    else:
        announcement = await client.get_channel(publicchannel).send('{} has been executed, but does not die.'.format(await common_name(person))) # announcement

    isExecutionToday = True # there has now been an execution
    await store_status()

    # Resolve day end
    if day_end:
        await end_day(user)
    return

async def exile(user, argument):
    # Exiles a player

    # Determine player
    players = [player for player in bggserver.members if await is_player(player)]
    person = await select_player(user, argument, players, origin = 'exile')
    if person == None:
        return

    # Check is person is traveler
    if not await is_role(person, travelerrole):
        await user.send('{} is not a traveler.'.format(await common_name(person)))
        return

    # Check if person dies
    death = await yes_no(user,'Does {} die'.format(await common_name(person)))
    if death == None:
        return

    # Announce execution
    if death:
        announcement = await client.get_channel(publicchannel).send('{} has been exiled.'.format(await common_name(person))) # announcement
        await announcement.pin() # pin
        await kill(user, person.name, suppress=True)
    else:
        announcement = await client.get_channel(publicchannel).send('{} has been exiled, but does not die.'.format(await common_name(person)))

async def revive(user, argument):
    # Revives a player

    # Determine player
    players = [player for player in bggserver.members if await is_player(player)]
    person = await select_player(user, argument, players, origin = 'revive')
    if person == None:
        return

    # Check if dead
    if not await is_role(person, ghostrole):
        await user.send('{} is already alive.'.format(await common_name(person)))
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
            role2 = rl
            break

    # Remove roles
    await bggserver.get_member(person.id).remove_roles(role, role2)

    # Announce ressurection
    announcement = await client.get_channel(publicchannel).send('{} has come back to life.'.format(await common_name(person))) # announcement
    await announcement.pin()

async def make_inactive(user, argument):
    # Marks a player as inactive.
    global notActive
    global canNominate


    # Determine player
    players = [player for player in bggserver.members if await is_player(player)]
    person = await select_player(user, argument, players, origin = 'makeinactive')
    if person == None:
        return

    # Find inactive role
    role = None
    for rl in bggserver.roles:
        if rl.name == inactiverole:
            role = rl
            break

    # Mark as inactive
    await person.add_roles(role)
    await user.send('{} has been marked as inactive.'.format(await common_name(person)))
    if person in notActive:
        await make_active(person)
    if person in canNominate:
        canNominate.remove(person)
    return

async def undo_inactive(user, argument):
    # Marks a player as active.

    # Determine player
    players = [player for player in bggserver.members if await is_player(player)]
    person = await select_player(user, argument, players, origin = 'undoinactive')
    if person == None:
        return

    # Find inactive role
    role = None
    for rl in bggserver.roles:
        if rl.name == inactiverole:
            role = rl
            break

    # Mark as inactive
    await person.remove_roles(role)
    await user.send('{} has been marked as active.'.format(await common_name(person)))
    if person not in canNominate:
        canNominate.append(person)
    return


### Event Handling
@client.event
async def on_ready():
    # On login

    # Global variables
    global isPmsOpen # bool - are pms open
    global isNomsOpen # bool - are nominations open
    global isDay # bool - is it the day
    global isExecutionToday # bool - has there been an execution today
    global notActive # list - players who have not spoken today
    global canNominate # list - players who can nominate today
    global canBeNominated # list - players who can be nominated today
    global hasSkipped # list - players who have skipped today
    global bggserver # abc - the main server object
    try:
        file = open("status.pckl","rb")
        isPmsOpen, isNomsOpen, isDay, isExecutionToday = pickle.load(file)
        file.close()
    except Exception:
        isPmsOpen = False
        isNomsOpen = False
        isDay = False
        isExecutionToday = False

    notActive = []
    canNominate = []
    canBeNominated = []
    hasSkipped = []
    bggserver = client.get_guild(bggid)

    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await update_presence(client)

@client.event
async def on_message(message):
    # Handles messages on reception

    # Don't respond to self
    if message.author == client.user:
        return

    # Public Channel
    if message.channel.id == publicchannel:

        # Update activity
        if isDay:
            if (message.author in notActive):
                await make_active(message.author)
        return

    # Check if not dm
    if message.guild != None:
        return

    # Check if command
    elif message.content.startswith(',') or message.content.startswith('@'):

        # Generate command and arguments
        if ' ' in message.content:
            command = message.content[1:message.content.index(' ')]
            argument = message.content[message.content.index(' ') + 1:]
        else:
            command = message.content[1:]
            argument = ''

        # Opens pms
        if command == 'openpms':
            if not await is_gamemaster(message.author): # check permissions
                await message.author.send('You don\'t have permission to open PMs.')
                return
            await open_pms(message.author)
            return

        # Opens nominations
        elif command == 'opennoms':
            if not await is_gamemaster(message.author): # check permissions
                await message.author.send('You don\'t have permission to open nominations.')
                return
            await open_noms(message.author)
            return

        # Opens pms and nominations
        elif command == 'open':
            if not await is_gamemaster(message.author): # check permissions
                await message.author.send('You don\'t have permission to open PMs and nominations.')
                return
            await open_pms(message.author)
            await open_noms(message.author)
            return

        # Closes pms
        elif command == 'closepms':
            if not await is_gamemaster(message.author): #check permissions
                await message.author.send('You don\'t have permission to close PMs.')
                return
            await close_pms(message.author)
            return

        # Closes nominations
        elif command == 'closenoms':
            if not await is_gamemaster(message.author): # check permissions
                await message.author.send('You don\'t have permission to close nominations.')
                return
            await close_noms(message.author)
            return

        # Closes pms and nominations
        elif command == 'close':
            if not await is_gamemaster(message.author): # check permissions
                await message.author.send('You don\'t have permission to close PMs and nominations.')
                return
            await close_pms(message.author)
            await close_noms(message.author)
            return

        # Starts day
        elif command == 'startday':
            if not await is_gamemaster(message.author): # check permissions
                await message.author.send('You don\'t have permission to start the day.')
                return
            await start_day(message.author, argument)
            return

        # Ends day
        elif command == 'endday':
            if not await is_gamemaster(message.author): # check permissions
                await message.author.send('You don\'t have permission to end the day.')
                return
            await end_day(message.author)
            return

        # Kills a player
        elif command == 'kill':
            if not await is_gamemaster(message.author): # check permissions
                await message.author.send('You don\'t have permission to kill players.')
                return
            await kill(message.author, argument)
            return

        # Executes a player
        elif command == 'execute':
            if not await is_gamemaster(message.author): # check permissions
                await message.author.send('You don\'t have permission to execute players.')
                return
            await execute(message.author, argument)
            return

        # Exiles a traveler
        elif command == 'exile':
            if not await is_gamemaster(message.author): # check permissions
                await message.author.send('You don\'t have permission to exile travelers.')
                return
            await exile(message.author, argument)
            return

        # Revives a player
        elif command == 'revive':
            if not await is_gamemaster(message.author): # check permissions
                await message.author.send('You don\'t have permission to revive players.')
                return
            await revive(message.author, argument)
            return

        # Nominates
        elif command == 'nominate':
            if not await is_gamemaster(message.author): # check permissions
                await message.author.send('You don\'t have permission to use @nominate.')
                return
            await nominate(message.author, argument)
            return

        elif command == 'makeinactive':
            if not await is_gamemaster(message.author): # check permissions
                await message.author.send('You don\'t have permission to make players inactive.')
                return
            await make_inactive(message.author, argument)
            return

        elif command == 'undoinactive':
            if not await is_gamemaster(message.author): # check permissions
                await message.author.send('You don\'t have permission to make players active.')
                return
            await undo_inactive(message.author, argument)
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
                await message.author.send('PMs are closed.')
                return

            if not await is_player(message.author): # Check permissions
                await message.author.send('You are not in the game. You may not send messages.')
                return

            await pm(argument,message.author)
            return

        # Help dialogue
        elif command == 'help':
            await message.author.send('**Commands:**\nopenpms: Opens pms\nopennoms: Opens noms\nopen: Opens pms and noms\nclosepms: Closes pms\nclosenoms: Closes noms\nclose: Closes pms and noms\nstartday <<players>>: Starts the day, killing players\nendday: Ends the day\nkill <<players>>: Kills players\nexecute <<player>>: Executes player\nexile <<traveler>>: Exiles traveler\nrevive <<player>>: revives player\nnominate <<player>>: Nominates player\nmakeinactive <<player>>: Considers player as automatically active for opening nominations.\nundoinactive: Undoes makeinactive.\n\nclear: Clears previous messages\nnotactive: Lists players yet to speak\ncannominate: Lists who can nominate today\ncanbenominated: Lists who can be nominated today\nmessage <<player>>: Privately messages player\npm <<player>>: Privately messages player\nhelp: Displays this dialogue\n\nCommand keys: @ and ,\nArgument separator: \', \'')
            return

        # Command unrecognized
        else:
            await message.author.send('Command {} not recognized. For a list of commands, type @help.'.format(command))

@client.event
async def on_message_edit(before, after):
    # Handles messages on modification
    global hasSkipped

    # On pin
    if after.channel == client.get_channel(publicchannel) and before.pinned == False and after.pinned == True:

        # Nomination
        if 'nominate ' in after.content.lower():
            await nominate(after.author, after.content[after.content.lower().index('nominate ') + 9:], message=after, location=client.get_channel(publicchannel))
            return

        # Skip
        elif 'skip' in after.content.lower():
            hasSkipped.append(after.author)
            if len([x for x in canNominate if x not in hasSkipped]) == 1:
                for memb in bggserver.members:
                    if await is_gamemaster(memb):
                        await memb.send('Just waiting on {} to nominate or skip.'.format(str([x for x in canNominate if x not in hasSkipped][0])))
            if len([x for x in canNominate if x not in hasSkipped]) == 0:
                print('test')
                for memb in bggserver.members:
                    if await is_gamemaster(memb):
                        await memb.send('Everyone has nominated or skipped!')
            return

    # On unpin
    elif after.channel == client.get_channel(publicchannel) and before.pinned == True and after.pinned == False:

        # Unskip
        if 'skip' in after.content.lower():
            if after.author in hasSkipped:
                hasSkipped.remove(after.author)
            return


### Loop
while True:
    client.run(TOKEN)
    print('end')
    time.sleep(5)
