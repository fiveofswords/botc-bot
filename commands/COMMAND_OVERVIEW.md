Here is a comprehensive list of all the **bot commands** found in `bot_impl.py`, including:

- **What the command does**
- **Arguments it takes (with differences based on role)**
- **How the role of the person running the command affects behavior** (with explicit notes for Player, Storyteller,
  Observer, Traveler, Ghost, and additional roles where relevant)
- **Special notes** for any command where behavior/arguments vary depending on user role or additional roles (traveler,
  ghost, etc).

---

# **Bot Command List with Role-based Details**

---

## 1. **startgame**

- **Who:** Storyteller only
- **Arguments:** None (prompts for seating order, roles, etc via follow-up)
- **Behavior:** Starts a new game. Only available if there is no ongoing game.
- **Role effect:** Only storytellers can run this command.

---

## 2. **endgame \<team\>**

- **Who:** Storyteller only
- **Arguments:** team ("good", "evil", or "tie")
- **Behavior:** Ends the current game and announces the winner.
- **Role effect:** Only storytellers can run this command.

---

## 3. **startday [\<players killed\>]**

- **Who:** Storyteller only
- **Arguments:** Optional space-separated list of players to kill at start of day.
- **Behavior:** Starts the day, optionally killing specified players.
- **Role effect:** Only storytellers can run this command. If arguments are provided, only Storyteller can specify
  players to kill.

---

## 4. **endday**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Ends the day, moves to night.
- **Role effect:** Only storytellers can run this command.

---

## 5. **kill \<player\>**

- **Who:** Storyteller only
- **Arguments:** player
- **Behavior:** Kills a player (sets them as a ghost).
- **Role effect:** Only storytellers can run this command. If the player is already dead, a warning is sent.

---

## 6. **execute \<player\>**

- **Who:** Storyteller only
- **Arguments:** player
- **Behavior:** Executes a player (special kill, e.g. via vote).
- **Role effect:** Only storytellers can run this command.

---

## 7. **exile \<traveler\>**

- **Who:** Storyteller only
- **Arguments:** traveler (must be a Traveler role)
- **Behavior:** Exiles a traveler (removes them from game).
- **Role effect:** Only storytellers can run, and only on travelers.

---

## 8. **revive \<player\>**

- **Who:** Storyteller only
- **Arguments:** player
- **Behavior:** Revives a dead player.
- **Role effect:** Only storytellers can run. Only works on ghosts.

---

## 9. **changerole \<player\>**

- **Who:** Storyteller only
- **Arguments:** player (then prompted for new role)
- **Behavior:** Changes a player's role.
- **Role effect:** Only storytellers can run.

---

## 10. **changealignment \<player\>**

- **Who:** Storyteller only
- **Arguments:** player (then prompted for new alignment)
- **Behavior:** Changes a player's alignment (good/evil).
- **Role effect:** Only storytellers can run.

---

## 11. **changeability \<player\>**

- **Who:** Storyteller only
- **Arguments:** player (then prompted for new ability role)
- **Behavior:** Adds a new ability (for AbilityModifier characters, e.g. Apprentice).
- **Role effect:** Only storytellers can run; only works for AbilityModifier characters.

---

## 12. **removeability \<player\>**

- **Who:** Storyteller only
- **Arguments:** player
- **Behavior:** Removes a modified ability (for AbilityModifier characters).
- **Role effect:** Only storytellers can run; only works for AbilityModifier characters.

---

## 13. **givedeadvote \<player\>**

- **Who:** Storyteller only
- **Arguments:** player
- **Behavior:** Adds a dead vote to a player.
- **Role effect:** Only storytellers can run.

---

## 14. **removedeadvote \<player\>**

- **Who:** Storyteller only
- **Arguments:** player
- **Behavior:** Removes a dead vote from a player.
- **Role effect:** Only storytellers can run.

---

## 15. **poison \<player\>**

- **Who:** Storyteller only
- **Arguments:** player
- **Behavior:** Poisons a player.
- **Role effect:** Only storytellers can run.

---

## 16. **unpoison \<player\>**

- **Who:** Storyteller only
- **Arguments:** player
- **Behavior:** Unpoisons a player.
- **Role effect:** Only storytellers can run.

---

## 17. **cancelnomination**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Cancels the current nomination/vote.
- **Role effect:** Only storytellers can run.

---

## 18. **setdeadline \<time\>**

- **Who:** Storyteller only
- **Arguments:** time (e.g., "HH:MM", "+2h30m", unix timestamp)
- **Behavior:** Sets a deadline for nominations.
- **Role effect:** Only storytellers can run.

---

## 19. **messagetally \<message_id\>**

- **Who:** Storyteller only
- **Arguments:** message ID
- **Behavior:** Reports message count tallies between pairs of players since a particular message.
- **Role effect:** Only storytellers can run.

---

## 20. **checkin \<players\>**

- **Who:** Storyteller only
- **Arguments:** space-separated list of players
- **Behavior:** Marks specified players as checked in.
- **Role effect:** Only storytellers can run. Multiple space-separated players allowed.

---

## 21. **undocheckin \<players\>**

- **Who:** Storyteller only
- **Arguments:** space-separated list of players
- **Behavior:** Marks specified players as not checked in.
- **Role effect:** Only storytellers can run. Multiple space-separated players allowed.

---

## 22. **makeinactive \<player\>**

- **Who:** Storyteller only
- **Arguments:** player
- **Behavior:** Marks a player as inactive.
- **Role effect:** Only storytellers can run.

---

## 23. **undoinactive \<player\>**

- **Who:** Storyteller only
- **Arguments:** player
- **Behavior:** Marks a player as active again.
- **Role effect:** Only storytellers can run.

---

## 24. **addtraveler \<player\>**

- **Who:** Storyteller only
- **Arguments:** player (then prompted for role, position, alignment)
- **Behavior:** Adds a player as a traveler.
- **Role effect:** Only storytellers can run.

---

## 25. **removetraveler \<player\>**

- **Who:** Storyteller only
- **Arguments:** player
- **Behavior:** Removes a traveler from the game.
- **Role effect:** Only storytellers can run.

---

## 26. **reseat \<players\>**

- **Who:** Storyteller only
- **Arguments:** prompted for new seating order (list of players)
- **Behavior:** Changes seating order.
- **Role effect:** Only storytellers can run.

---

## 27. **resetseats**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Resets the seating chart to current.
- **Role effect:** Only storytellers can run.

---

## 28. **whispermode \<mode\>**

- **Who:** Storyteller only
- **Arguments:** mode ("all", "neighbors", "storytellers")
- **Behavior:** Sets the whisper mode for the game.
- **Role effect:** Only storytellers can run.

---

## 29. **openpms**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Opens PMs for the day.
- **Role effect:** Only storytellers can run.

---

## 30. **opennoms**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Opens nominations for the day.
- **Role effect:** Only storytellers can run.

---

## 31. **open**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Opens both PMs and nominations.
- **Role effect:** Only storytellers can run.

---

## 32. **closepms**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Closes PMs for the day.
- **Role effect:** Only storytellers can run.

---

## 33. **closenoms**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Closes nominations for the day.
- **Role effect:** Only storytellers can run.

---

## 34. **close**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Closes both PMs and nominations.
- **Role effect:** Only storytellers can run.

---

## 35. **setatheist \<true/false\>**

- **Who:** Storyteller only
- **Arguments:** true/false
- **Behavior:** Sets whether the Atheist is on the script (can storyteller be nominated?).
- **Role effect:** Only storytellers can run.

---

## 36. **automatekills \<true/false\>**

- **Who:** Storyteller only
- **Arguments:** true/false
- **Behavior:** Sets whether special kills (Riot, Golem, etc) are automated.
- **Role effect:** Only storytellers can run.

---

## 37. **enabletally**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Enables display of whisper counts.
- **Role effect:** Only storytellers can run.

---

## 38. **disabletally**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Disables display of whisper counts.
- **Role effect:** Only storytellers can run.

---

## 39. **notactive**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Lists players who have not yet spoken this day (are not active).
- **Role effect:** Only storytellers can run.

---

## 40. **tocheckin**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Lists players who have not checked in.
- **Role effect:** Only storytellers can run.

---

## 41. **adjustvotes \<amnesiac\> \<target\> \<multiplier\>**

- **Who:** Storyteller only
- **Arguments:** amnesiac, target, multiplier (int)
- **Behavior:** Amnesiac (special character) multiplies another player's vote.
- **Role effect:** Only storytellers can run.

---

## 42. **welcome \<player\>**

- **Who:** Storyteller only
- **Arguments:** player
- **Behavior:** Sends a welcome message to a player and creates their ST channel if missing.
- **Role effect:** Only storytellers can run.

---

## 43. **vote \<yes/no\>**

- **Who:** Player (and Storyteller in special mode)
- **Arguments:** yes/y/no/n
- **Behavior:**
    - **Player:** Casts their vote if it's their turn.
    - **Storyteller:** Prompted for "Whose vote is this?" and can vote on anyone's behalf (not via arguments).
- **Role effect:** Only the player whose turn it is can vote, unless storyteller is using the override.
- **Ghost:** If a player is a ghost, special restrictions may apply (e.g., only Voudon/dead can vote in some cases).

---

## 44. **presetvote/prevote \<yes/no/0/1/2\>**

- **Who:** Player, Storyteller (special override)
- **Arguments:**
    - **Player:** yes/y/no/n/0/1/2
    - **Storyteller:** Prompted for "Whose vote is this?" and can set for anyone (not via arguments).
- **Behavior:** Sets a preset vote for the next voting round.
- **Role effect:** Storyteller can set anyone's; player can only set their own.

---

## 45. **cancelpreset/cancelprevote**

- **Who:** Player, Storyteller (special override)
- **Arguments:**
    - **Player:** None
    - **Storyteller:** Prompted for "Whose vote do you want to cancel?" (not via arguments).
- **Behavior:** Cancels preset vote for self (player), or for anyone (storyteller).

---

## 46. **defaultvote [\<yes/no\> [\<minutes\>]]**

- **Who:** Player only
- **Arguments:**
    - None: Removes default vote if set.
    - \<yes/no\> [\<minutes\>]: Sets default vote and optional duration.
- **Role effect:** Only players can set/remove their default votes.

---

## 47. **pm/message \<player\>**

- **Who:** Player only
- **Arguments:** player
- **Behavior:** Sends a DM (whisper) to another player if PMs are open and allowed by whisper mode.
- **Role effect:** Only players can run; only when PMs are open.

---

## 48. **history [\<player\>] or [\<player1\> \<player2\>]**

- **Who:** Everyone, with different capabilities:
    - **Storyteller/Observer:** Can specify either one player (for all their messages) or two players (shows
      conversation between them).
    - **Player:** Only allowed to specify one player, which must be self or someone they've messaged.
- **Arguments:**
    - **Storyteller/Observer:** \<player\> or \<player1\> \<player2\>
    - **Player:** \<player\>
- **Role effect:** Storyteller/observer can see anyone's history, including between others. Players can only see their
  own message history with another player.

---

## 49. **search \<text\>**

- **Who:** Everyone, with different scope.
    - **Storyteller/Observer:** Searches all messages for text.
    - **Player:** Searches only their own messages.
- **Arguments:** text
- **Role effect:** Scope of search is restricted for players.

---

## 50. **whispers [\<player\>]**

- **Who:** Everyone, with different arguments:
    - **Storyteller:** Must specify \<player\> (shows whisper counts for that player).
    - **Player:** No argument (shows own whisper counts).
- **Arguments:**
    - **Storyteller:** \<player\> (required)
    - **Player:** None
- **Role effect:** Argument required for storyteller, forbidden for player.

---

## 51. **info \<player\>**

- **Who:** Storyteller only
- **Arguments:** player
- **Behavior:** Shows detailed info about a player (character, alignment, votes, etc).
- **Role effect:** Only storyteller can run.

---

## 52. **votehistory**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Shows all nominations and votes for all days.
- **Role effect:** Only storyteller can run.

---

## 53. **grimoire**

- **Who:** Storyteller only
- **Arguments:** None
- **Behavior:** Shows the current grimoire (all player roles/status).
- **Role effect:** Only storyteller can run.

---

## 54. **clear**

- **Who:** Everyone
- **Arguments:** None
- **Behavior:** Sends a bunch of whitespace to "clear" previous messages for the user.
- **Role effect:** None.

---

## 55. **cannominate**

- **Who:** Everyone
- **Arguments:** None
- **Behavior:** Lists players who have not nominated or skipped.
- **Role effect:** None, but only meaningful for active players.

---

## 56. **canbenominated**

- **Who:** Everyone
- **Arguments:** None
- **Behavior:** Lists players who can still be nominated.
- **Role effect:** None.

---

## 57. **makealias \<alias\> \<command\>**

- **Who:** Everyone
- **Arguments:** alias, command
- **Behavior:** Creates an alias for a command (per-user).
- **Role effect:** None.

---

## 58. **handup/handdown**

- **Who:** Player only
- **Arguments:** None
- **Behavior:** Raises/lowers the player's hand for voting.
- **Role effect:** Only players can use.

---

## 59. **lastactive**

- **Who:** Storyteller/Observer
- **Arguments:** None
- **Behavior:** Shows last active times for all players.
- **Role effect:** Only storyteller/observer can run.

---

## 60. **nominate \<player\>**

- **Who:** Player / Storyteller (in special mode)
- **Arguments:** player
- **Behavior:**
    - **Player:** Nominates another player for execution.
    - **Storyteller:** Can nominate on behalf of anyone, or the storytellers themselves (in Atheist game).
- **Role effect:** Only the current player can nominate, unless storyteller is overriding (details in code).
- **Ghost:** Ghosts generally cannot nominate, unless they're travelers or under special circumstances (e.g. Banshee).

---

---

# **Special Notes on Role Interactions and Argument Differences**

- **Storyteller (gamemaster_role):** Can run all commands, often with broader arguments or ability to specify any
  player.
- **Player (player_role):** Can mostly run commands affecting themselves; cannot specify other players for most
  commands. Ghost status, traveler status, and deadvote/inactive roles may restrict command effects.
- **Observer (observer_role):** Can run only a handful of info commands (history, lastactive, search).
- **Traveler (traveler_role):** Is a type of player; some commands (like exile) only operate on travelers.
- **Ghost (ghost_role):** Is a type of player; some commands behave differently if the player is dead (can't
  nominate/vote unless allowed).
- **Deadvote, Inactive:** Only affect logic for certain commands, e.g. deadvote for voting, inactive for reminders.

---

# **Summary Table of Role-Specific Argument Differences**

| Command      | Storyteller Arguments               | Player Arguments             | Observer Arguments    | Notes                  |
|--------------|-------------------------------------|------------------------------|-----------------------|------------------------|
| whispers     | \<player\> (required)               | none (self only)             | (not available)       |                        |
| history      | \<player\> or \<p1\> \<p2\>         | \<player\> (self+other only) | same as storyteller   |                        |
| search       | \<text\> (full search)              | \<text\> (self search only)  | same as storyteller   |                        |
| vote         | \<yes/no\> (anyone by prompt)       | \<yes/no\> (own only)        | (not available)       | ST prompted for player |
| presetvote   | \<yes/no/0/1/2\> (anyone by prompt) | \<yes/no/0/1/2\> (own only)  | (not available)       | ST prompted for player |
| cancelpreset | (prompt for player)                 | (own only)                   | (not available)       | ST prompted for player |
| info         | \<player\>                          | N/A                          | N/A                   |                        |
| pm/message   | N/A                                 | \<player\>                   | N/A                   |                        |
| handup/down  | N/A                                 | none                         | N/A                   |                        |
| makealias    | \<alias\> \<command\>               | \<alias\> \<command\>        | \<alias\> \<command\> |                        |

---

If you want this as a CSV or a more compact table, or want to know about a specific command, let me know!