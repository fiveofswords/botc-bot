# BOTC-bot
A WIP bot for playing Blood on the Clocktower.

## config.py
You'll want a `config.py` file in the root directory with the following variables declared
```
channelid = 1028299479348154418
whisperchannelid = 1251894128602779728
serverid = 721446589750706266
playerName = "player"
travelerName = "traveler"
ghostName = "ghost"
deadVoteName = "deadVote"
gamemasterName = "gamemaster"
inactiveName = "inactive"
observerName = "observer"

prefixes = (',', '@')
```
Switch the values for your own server's IDs and names.

## Building and running using docker
To build the docker image, run the following command in the root directory

```docker build -t botc .```

When the image is built, you can run the bot using the following command

```docker run -v .:/app -v $(pwd)/bot_configs/bot-name.py:/app/config.py -d --name bot-name botc```
