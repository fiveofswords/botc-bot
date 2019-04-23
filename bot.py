# Work with Python 3.6



class UserNotFoundException(Exception):

    def __init__(self,*args,**kwargs):

        Exception.__init__(self,*args,**kwargs)



import discord

import os, time

from config import *

global pmsopen
global nomsopen
global isday
global notactive
notactive = []
pmsopen = False
nomsopen = False
isday = False

with open(os.path.dirname(os.path.realpath(__file__))+'/token.txt') as tokenfile:

    TOKEN = tokenfile.readline().strip()



client = discord.Client()

async def update_presence(client):
    clopen = ["Closed","Open"]
    await client.change_presence(game=discord.Game(name="PMs "+clopen[pmsopen]+", Nominations "+clopen[nomsopen]+"!"))
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
    global nomsopen
    global isday
    global notactive
    bggserver = client.get_server(bggid)
    if message.author == client.user:

        return
    # we do not want the bot to reply to itself
    if message.channel.id == publicchannel:
        if (message.author in notactive) and isday:
            notactive.remove(message.author)
            if len(notactive) == 1:
                for memb in bggserver.members:
                    if gamemasterrole in [role.name for role in memb.roles]:
                        await client.send_message(memb, "Just waiting on "+notactive[0].name+" to speak.")
            if len(notactive) == 0:
                for memb in bggserver.members:
                    if gamemasterrole in [role.name for role in memb.roles]:
                        await client.send_message(memb, "Everyone has spoken!")
        return

    if message.server != None:

        return

    if message.content.startswith(',openpms') or message.content.startswith('@openpms'):

        if gamemasterrole not in [g.name for g in bggserver.get_member(message.author.id).roles]:

            await client.send_message(message.author,'You don\'t have permission to open PMs.')

            return

        pmsopen = True
        await update_presence(client)
        for user in bggserver.members:
            if gamemasterrole in [r.name for r in user.roles]:
                await client.send_message(user,'PMs are now open.')
        # await client.send_message(message.author,'PMs are now open.')
        #await client.send_message(publicchannel, 'PMs are now open.')

    elif message.content.startswith(',opennominations') or message.content.startswith('@opennominations'):
        if gamemasterrole not in [g.name for g in bggserver.get_member(message.author.id).roles]:
            await client.send_message(message.author, 'You don\'t have permission to open nominations.')

            return

        nomsopen = True
        await update_presence(client)
        for user in bggserver.members:
            if gamemasterrole in [r.name for r in user.roles]:
                await client.send_message(user,'Nominations are now open.')
    elif message.content.startswith(',closenominations') or message.content.startswith('@closenominations'):
        if gamemasterrole not in [g.name for g in bggserver.get_member(message.author.id).roles]:
            await client.send_message(message.author, 'You don\'t have permission to close nominations.')

            return

        nomsopen = False
        await update_presence(client)
        for user in bggserver.members:
            if gamemasterrole in [r.name for r in user.roles]:
                await client.send_message(user,'Nominations are now closed.')
    elif message.content.startswith(',closepms') or message.content.startswith('@closepms'):

        if gamemasterrole not in [g.name for g in bggserver.get_member(message.author.id).roles]:
            await client.send_message(message.author, 'You don\'t have permission to close PMs.')

            return

        pmsopen = False
        await update_presence(client)
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



    elif message.content.startswith(",startday") or message.content.startswith("@startday"):
        if gamemasterrole not in [role.name for role in bggserver.get_member(message.author.id).roles]:
            await client.send_message(message.author, "You do not have permission to start the day.")
        else:
            pmsopen = True
            isday = True
            roleobj = None
            await update_presence(client)
            for rl in bggserver.roles:
                if rl.name == playerrole:
                    roleobj = rl
                    break
            await client.send_message(client.get_channel(publicchannel),roleobj.mention+" wake up!")
            notactive = [player for player in bggserver.members if ((playerrole in [rll.name for rll in player.roles]) and (gamemasterrole not in [rll.name for rll in player.roles]))]

    elif message.content.startswith(",endday") or message.content.startswith("@endday"):
        if gamemasterrole not in [role.name for role in bggserver.get_member(message.author.id).roles]:
            await client.send_message(message.author, "You do not have permission to end the day.")
        else:
            pmsopen = False
            isday = False
            nomsopen = False
            roleobj = None
            await update_presence(client)
            for rl in bggserver.roles:
                if rl.name == playerrole:
                    roleobj = rl
                    break
            await client.send_message(client.get_channel(publicchannel),roleobj.mention+" go to sleep!")
    elif message.content.startswith(",notactive") or message.content.startswith("@notactive"):
        send = "These players have not spoken:\n"
        for user in notactive:
            send += (user.nick or user.name) + "\n"

        if not isday:
            await client.send_message(message.author, "It's not day right now!")
        elif len(send)>31:
            await client.send_message(message.author, send)
        else:
            await client.send_message(message.author, "Everyone has spoken!")

@client.event

async def on_ready():

    print('Logged in as')

    print(client.user.name)

    print(client.user.id)

    print('------')
    await update_presence(client)


@client.event

async def on_message_edit(before, after):
    global pmsopen
    global nomsopen
    global isday
    bggserver = client.get_server(bggid)
    if after.channel == client.get_channel(publicchannel) and before.pinned == False and after.pinned == True and playerrole in [roll.name for roll in after.author.roles]:
        if "nominate " in after.content.strip().lower():
            if nomsopen:
                users = []
                name = after.content.strip().lower().split("nominate")[-1].strip()
                for user in bggserver.members:
                    if ((user.nick != None and name == user.nick.lower()[:len(name)]) or name == user.name.lower()[:len(name)])  and (playerrole in [role.name for role in user.roles]):
                        users.append(user)
                if len(users) == 1:
                    await client.send_message(client.get_channel(publicchannel), users[0].mention + " has been nominated.")
                    nomsopen = False
                    pmsopen = False
                    await update_presence(client)
                else:
                    await client.send_message(client.get_channel(publicchannel), "User not found. Try again.")
                    await client.unpin_message(after)
            else:
                await client.send_message(client.get_channel(publicchannel), "Nominations are closed.")
                await client.unpin_message(after)


while True:
    client.run(TOKEN)
    print('end')
    time.sleep(5)
