# Work with Python 3.6

class UserNotFoundException(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

import discord
bggid = '421432788894482434'
publicchannel = '430792054683992074'
with open('../token.txt') as tokenfile:
    TOKEN = tokenfile.readline().strip()

client = discord.Client()

async def sendGMpublic(frm, to, content, server):
    master = None
    for role in server.roles:
        if role.name == "Game Master":
            master = role
            break

    for member in server.members:
        if master in member.roles and member != frm and member != to:
            gmcopy = await client.send_message(member, "Message sent from {0} to {1}: ".format(frm.name,to.name)+content)

    pubcopy = await client.send_message(client.get_channel(publicchannel), "**{0}** > **{1}**".format(frm.name,to.name))

async def choices(possibilities,message):
    pickone = await client.send_message(message.author,"Which user would you like to send the message to?")
    for index,u in enumerate(possibilities):
        await client.send_message(message.author,"({0}). {1}".format(index+1,u.name))
    choice = await client.wait_for_message(timeout=200, author=message.author, channel=pickone.channel)
    if choice == None:
        await client.send_message(message.author,"Timed out.")
        return
    if choice.content.lower() == 'cancel':
        await client.send_message(message.author,"Cancelled.")
        return
    try:
        a = possibilities[int(choice.content)-1]
        return possibilities[int(choice.content)-1]
    except Exception:
        temp = []
        for i in possibilities:
            if (i.nick != None and choice.content.lower() in i.nick.lower()) or choice.content.lower() in i.name.lower():
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
    bggserver = client.get_server(bggid)
    # we do not want the bot to reply to itself
    if message.author == client.user or message.server != None:
        return

    if message.content.startswith('!message'):
        try:
            name = message.content[8:].strip()
            possibilities = []
            for person in bggserver.members:
                if (person.nick != None and name.lower() == person.nick.lower()[:len(name)]) or name.lower() == person.name.lower()[:len(name)]:
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

            replytxt = "Messaging {}. What would you like to send?".format(person.name)
            reply = await client.send_message(message.author, replytxt)
            userresponse = await client.wait_for_message(timeout=200, author=message.author, channel=reply.channel)
            if userresponse == None:
                end = await client.send_message(message.author, "Message timed out!")
                return
            if userresponse.content.lower() == 'cancel':
                end = await client.send_message(message.author, "Message cancelled!")
                return
            send = await client.send_message(person, "Message from {}: ".format(message.author.name)+userresponse.content)
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

client.run(TOKEN)
