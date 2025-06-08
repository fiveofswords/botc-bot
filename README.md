# BOTC-bot

A Discord bot for playing Blood on the Clocktower.

## Features

- Full game management (setup, day/night phases, voting, nominations)
- Character ability automation and tracking
- Player management and role assignment
- Whisper mode and private communications
- Traveler voting system
- Info channel with seating order updates
- Comprehensive testing suite with 400+ tests
- Multiple environment support for different servers

## Configuration

The bot uses environment-specific configurations. You can either:

1. Use one of the existing configs in `bot_configs/` (George.py, Leo.py, Quinn.py, TipToe.py)
2. Create a custom `config.py` file in the root directory with the following variables:
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

## Development Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create required files for testing (these are not checked into git)
echo "dummy_token_for_testing" > token.txt  # Add your actual bot token for production
cp bot_configs/George.py config.py  # Or create custom config.py as shown above

# Run tests
python -m pytest

# Run with coverage
python -m pytest --cov=. --cov-report=term
```

**Note:** `token.txt` and `config.py` are required for imports but tests use mocking so actual values don't matter for
testing.

See `CLAUDE.md` for detailed development guidelines and project structure.

## Building and running using docker
To build the docker image, run the following command in the root directory of the project. This will make an image with tag name botc.

```docker build -t botc .```

When the image is built, you can run the bot using the following command.
Set the BOT_NAME variable or replace `${BOT_NAME}` with the name of the bot you want to run, and `bot_configs/${BOT_NAME}.py` with the path to the bot's configuration file.

```docker run -v $(dirname $(pwd))/preferences.json:/preferences.json -v $(pwd):/app -v $(pwd)/bot_configs/${BOT_NAME}.py:/app/config.py -d --name ${BOT_NAME} botc```

Mounting volumes via relative path is not supported in docker except for the current directory. If you want to mount a volume from a different directory, you need to provide the full path, which $(pwd) gets at.


To enter the shell for one of the bots:
```docker exec -it ${BOT_NAME} /bin/bash```