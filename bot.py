# Work with Python 3.6



class UserNotFoundException(Exception):

    def __init__(self,*args,**kwargs):

        Exception.__init__(self,*args,**kwargs)



import discord

import os, time

bggid = '421432788894482434'

publicchannel = '510551306361110535'

gamemasterrole = 'Storyteller'

playerrole = 'Townsfolk (Clocktower)'

global pmsopen
pmsopen = False

with open(os.path.dirname(os.path.realpath(__file__))+'/token.txt') as tokenfile:

    TOKEN = tokenfile.readline().strip()



client = discord.Client()


async def sendGMpublic(frm, to, content, server):

    master = None

    for role in server.roles:

        if role.name == gamemasterrole:

            master = role

            break



    for member in server.members:

        if master in member.roles and member != frm and member != to:

            gmcopy = await client.send_message(member, "**[**{0} **>** {1}**]** ".format(server.get_member(frm.id).nick if server.get_member(frm.id).nick else frm.name, to.nick if to.nick else to.name)+content)



    pubcopy = await client.send_message(client.get_channel(publicchannel), "**{0}** > **{1}**".format(server.get_member(frm.id).nick if server.get_member(frm.id).nick else frm.name,to.nick if to.nick else to.name))



async def choices(possibilities,message):
    messagetext = "Which user would you like to send the message to?\n"
    # pickone = await client.send_message(message.author,"Which user would you like to send the message to?")

    for index,u in enumerate(possibilities):
        messagetext += "({0}). {1}\n".format(index+1,u.nick if u.nick else u.name)
        # await client.send_message(message.author,"({0}). {1}".format(index+1,u.nick if u.nick else u.name))

    pickone = await client.send_message(message.author,messagetext)
    choice = await client.wait_for_message(timeout=200, author=message.author, channel=pickone.channel)

    if choice == None:

        await client.send_message(message.author,"Timed out.")

        return

    if choice.content.lower() == 'cancel':

        await client.send_message(message.author,"Message cancelled!")

        return
    if choice.content.lower().startswith(',message') or choice.content.lower().startswith('@message'):
        return
    try:

        a = possibilities[int(choice.content)-1]

        return possibilities[int(choice.content)-1]

    except Exception:

        temp = []

        for i in possibilities:

            if ((i.nick != None and choice.content.lower() in i.nick.lower()) or choice.content.lower() in i.name.lower())  and playerrole in [g.name for g in i.roles]:

                temp.append(i)

        if len(temp) == 0:

            await client.send_message(message.author,"User not found. Try again.")

            return await choices(possibilities,message)

        elif len(temp) == 1:

            return temp[0]

        else:

            return await choices(temp,message)







@client.event

async def on_message(message):
    global pmsopen

    bggserver = client.get_server(bggid)

    # we do not want the bot to reply to itself

    if message.author == client.user or message.server != None:

        return

    if message.content.startswith(',openpms') or message.content.startswith('@openpms'):

        if gamemasterrole not in [g.name for g in bggserver.get_member(message.author.id).roles]:

            await client.send_message(message.author,'You don\'t have permission to open PMs.')

            return

        pmsopen = True
        await client.change_presence(game=discord.Game(name="PMs Open!"))
        for user in bggserver.members:
            if gamemasterrole in [r.name for r in user.roles]:
                await client.send_message(user,'PMs are now open.')
        # await client.send_message(message.author,'PMs are now open.')
        #await client.send_message(publicchannel, 'PMs are now open.')

    elif message.content.startswith(',closepms') or message.content.startswith('@closepms'):

        if gamemasterrole not in [g.name for g in bggserver.get_member(message.author.id).roles]:
            await client.send_message(message.author, 'You don\'t have permission to close PMs.')

            return

        pmsopen = False
        await client.change_presence(game=discord.Game(name="PMs Closed!"))
        for user in bggserver.members:
            if gamemasterrole in [r.name for r in user.roles]:
                await client.send_message(user,'PMs are now closed.')
        # await client.send_message(message.author, 'PMs are now closed.')
        #await client.send_message(publicchannel, 'PMs are now closed.')


    elif message.content.startswith(',clear') or message.content.startswith('@clear'):

        await client.send_message(message.author,"\u200B\n"*25+  "Clearing\n"+"\u200B\n"*25)

    # if message.content.startswith('!clear'):

    #     try:

    #         await client.purge_from(message.channel,limit=int(message.content[6:].strip()))

    #     except Exception:

    #         await client.purge_from(message.channel)

    elif message.content.startswith(',message') or message.content.startswith('@message'):

        if not pmsopen:

            await client.send_message(message.author, "Hydra wanted me to put a passive-aggressive message here, but I decided to be nice. PMs are closed, by the way.")

            return

        if playerrole not in [g.name for g in bggserver.get_member(message.author.id).roles]:
            await client.send_message(message.author, "You are not in the game. You may not send messages.")
            return

        try:

            name = message.content[8:].strip()

            possibilities = []

            for person in bggserver.members:

                if ((person.nick != None and name.lower() == person.nick.lower()[:len(name)]) or name.lower() == person.name.lower()[:len(name)]) and playerrole in [g.name for g in person.roles]:

                    possibilities.append(person)



            if len(possibilities) == 0:

                notfound = await client.send_message(message.author, "User not found. Try again!")

                return



            elif len(possibilities) > 1:

                person = await choices(possibilities,message)

                if person == None:

                    return









            elif len(possibilities) == 1:

                person = possibilities[0]



            replytxt = "Messaging {0}. What would you like to send?".format(person.nick if person.nick else person.name)

            reply = await client.send_message(message.author, replytxt)

            userresponse = await client.wait_for_message(timeout=200, author=message.author, channel=reply.channel)

            if userresponse == None:

                end = await client.send_message(message.author, "Message timed out!")

                return

            if userresponse.content.lower() == 'cancel':

                end = await client.send_message(message.author, "Message cancelled!")

                return

            if userresponse.content.lower().startswith(',message') or userresponse.content.lower().startswith('@message'):
                return

            send = await client.send_message(person, "Message from {0}: **".format(bggserver.get_member(message.author.id).nick if bggserver.get_member(message.author.id).nick else message.author.name)+userresponse.content+"**")

            await sendGMpublic(message.author,person,userresponse.content,bggserver)

            end = await client.send_message(message.author, "Message sent!")

            return

        except UserNotFoundException:

            await client.send_message(message.author, "User not found. Try again.")





@client.event

async def on_ready():

    print('Logged in as')

    print(client.user.name)

    print(client.user.id)

    print('------')
    if pmsopen == True:
        await client.change_presence(game=discord.Game(name="PMs Open!"))
    else:
        await client.change_presence(game=discord.Game(name="PMs Closed!"))



while True:
    client.run(TOKEN)
    print('end')
    time.sleep(5)
