# BOTC-bot
A bot for playing Blood on the Clocktower.

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
To build the docker image, run the following command in the root directory of the project. This will make an image with tag name botc.

```docker build -t botc .```

When the image is built, you can run the bot using the following command.
Replace `${BOT_NAME}` with the name of the bot you want to run, and `bot_configs/${BOT_NAME}.py` with the path to the bot's configuration file.

```docker run -v .:/app -v $(pwd)/bot_configs/${BOT_NAME}.py:/app/config.py -d --name ${BOT_NAME} botc```

Mounting volumes via relative path is not supported in docker except for the current directory. If you want to mount a volume from a different directory, you need to provide the full path, which $(pwd) gets at.
