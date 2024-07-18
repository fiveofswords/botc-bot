# BOTC-bot
A bot for playing Blood on the Clocktower.

## config.py
You'll want a `config.py` file in the root directory with the following variables declared
```
# Guild ID for Game Server
SERVER_ID = 721446589750706266 # Guild ID for Game Server
GAME_CATEGORY_ID = 1202456091057725550  # Category for in play player channels and game channels
HANDS_CHANNEL_ID = 1260773800400912545  # Hands ST Channel
OBSERVER_CHANNEL_ID = 1260773624101605466 # Observer Channel
INFO_CHANNEL_ID = 1260775601413816320  # Info Channel
WHISPER_CHANNEL_ID = 1251894128602779728 # Channel for player whispers
TOWN_SQUARE_CHANNEL_ID = 1028299479348154418 # Town Square
OUT_OF_PLAY_CATEGORY_ID = 1260776733674704997  # Category for out of play player channels

# Role Names
PLAYER_ROLE = "player"
TRAVELER_ROLE = "traveler"
GHOST_ROLE = "ghost"
DEAD_VOTE_ROLE = "deadVote"
STORYTELLER_ROLE = "gamemaster"
INACTIVE_ROLE = "inactive"
OBSERVER_ROLE = "observer"

# Channel Creation Metadata
CHANNEL_SUFFIX = 'test'

PREFIXES = (',', '@')
```
Switch the values for your own server's IDs and names.

## Building and running using docker
To build the docker image, run the following command in the root directory of the project. This will make an image with tag name botc.

```docker build -t botc .```

When the image is built, you can run the bot using the following command.
Replace `${BOT_NAME}` with the name of the bot you want to run, and `bot_configs/${BOT_NAME}.py` with the path to the bot's configuration file.

```docker run -v $(dirname $(pwd))/preferences.json:/preferences.json -v $(pwd):/app -v $(pwd)/bot_configs/${BOT_NAME}.py:/app/config.py -d --name ${BOT_NAME} botc```

Mounting volumes via relative path is not supported in docker except for the current directory. If you want to mount a volume from a different directory, you need to provide the full path, which $(pwd) gets at.
