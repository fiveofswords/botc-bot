# BOTC-bot
A WIP bot for playing Blood on the Clocktower.

## config.py
You'll want a `config.py` file in the root directory with the following variables declared
```
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

prefixes = (',', '@')
```
Switch the values for your own server's IDs and names.