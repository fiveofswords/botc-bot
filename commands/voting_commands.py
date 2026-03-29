"""Voting and nomination related commands."""

import discord
import asyncio

import model
import bot_client
import global_vars
from commands.command_enums import HelpSection, UserType, GamePhase
from commands.registry import registry, CommandArgument
from utils import player_utils, message_utils, character_utils, game_utils


@registry.command(
    name="cancelnomination",
    description="cancels the previous nomination",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def cancelnomination_command(message: discord.Message, argument: str):
    """Cancel the current nomination and vote."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="handup",
    description="Raise your hand during a vote",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def handup_command(message: discord.Message, argument: str):
    """Raise your hand during a vote."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="handdown",
    description="Lower your hand during a vote",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def handdown_command(message: discord.Message, argument: str):
    """Lower your hand during a vote."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="vote",
    description={
        UserType.STORYTELLER: "votes for the current player",
        UserType.PLAYER: "votes on an ongoing nomination"
    },
    help_sections=[HelpSection.DAY, HelpSection.PLAYER],
    user_types=[UserType.PLAYER, UserType.STORYTELLER],
    arguments={
        UserType.STORYTELLER: [],  # No arguments for storytellers
        UserType.PLAYER: [CommandArgument(("yes", "no"))]
    },
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def vote_command(message: discord.Message, argument: str):
    """Cast your vote (yes/no) if it's your turn."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="presetvote",
    description="submits a preset vote. will not work if it is your turn to vote. not recommended -- contact the storytellers instead",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER, UserType.STORYTELLER],
    aliases=["prevote"],
    arguments=[CommandArgument(("yes", "no"))],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=True
)
async def presetvote_command(message: discord.Message, argument: str):
    """Set a preset vote for the next voting round."""
    # Ported from bot_impl.py presetvote handling
    if global_vars.game is model.game.game.NULL_GAME:
        await message_utils.safe_send(message.author, "There's no game right now.")
        return

    if global_vars.game.isDay == False:
        await message_utils.safe_send(message.author, "It's not day right now.")
        return

    if global_vars.game.days[-1].votes == [] or global_vars.game.days[-1].votes[-1].done == True:
        await message_utils.safe_send(message.author, "There's no vote right now.")
        return

    # validate argument
    if (
        argument != "yes"
        and argument != "y"
        and argument != "no"
        and argument != "n"
        and argument not in ["0", "1", "2"]
    ):
        await message_utils.safe_send(message.author,
                                      f"{argument} is not a valid vote. Use 'yes', 'y', 'no', or 'n'.")
        return

    vote = global_vars.game.days[-1].votes[-1]
    voudon_in_play = model.game.vote.in_play_voudon()

    # Storyteller (gamemaster) path
    if global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
        msg = await message_utils.safe_send(message.author, "Whose vote is this?")
        try:
            reply = await bot_client.client.wait_for(
                "message",
                check=(lambda x: x.author == message.author and x.channel == msg.channel),
                timeout=200,
            )
        except asyncio.TimeoutError:
            await message_utils.safe_send(message.author, "Timed out.")
            return

        if reply.content.lower() == "cancel":
            await message_utils.safe_send(message.author, "Preset vote cancelled!")
            return

        reply_text = reply.content.lower()
        person = await player_utils.select_player(
            message.author, reply_text, global_vars.game.seatingOrder
        )
        if person is None:
            return

        player_banshee_ability = character_utils.the_ability(person.character, model.characters.Banshee)
        banshee_override = player_banshee_ability and player_banshee_ability.is_screaming

        if argument in ["0", "1", "2"]:
            if not banshee_override:
                await message_utils.safe_send(message.author, f"{argument} is not a valid vote for this player.")
                return
            vt = int(argument)
        else:
            yes_entered = argument == "yes" or argument == "y"
            vt = int(yes_entered) * (2 if banshee_override else 1)

        if voudon_in_play and person != voudon_in_play and not person.is_ghost and vt > 0:
            await message_utils.safe_send(message.author,
                                          "Voudon is in play. Only the Voudon and dead may vote. Consider killing this player before prevoting yes.")
            return

        await vote.preset_vote(person, vt, operator=message.author)
        if (banshee_override):
            await message_utils.safe_send(message.author, f"Successfully preset to {vt}!")
        else:
            await message_utils.safe_send(message.author, f"Successfully preset to {argument}!")
        if global_vars.game is not model.game.game.NULL_GAME:
            game_utils.backup("current_game.pckl")

        # Prompt for hand status (Storyteller context)
        try:
            hand_status_prompt_st = await message_utils.safe_send(message.author,
                                                                  f"Hand up or down for {person.display_name}? (up/down/cancel)")
            hand_status_choice_st = await bot_client.client.wait_for(
                "message",
                check=(lambda x: x.author == message.author and x.channel == hand_status_prompt_st.channel),
                timeout=200,
            )
            choice_content_st = hand_status_choice_st.content.lower()
            if choice_content_st == "up":
                person.hand_raised = True
                await message_utils.safe_send(message.author, f"{person.display_name}'s hand is now up.")
            elif choice_content_st == "down":
                person.hand_raised = False
                await message_utils.safe_send(message.author, f"{person.display_name}'s hand is now down.")
            elif choice_content_st == "cancel":
                await message_utils.safe_send(message.author, "Hand status change cancelled.")
            else:
                await message_utils.safe_send(message.author, "Invalid choice. Hand status not changed.")

            if choice_content_st in ["up", "down"]:
                await global_vars.game.update_seating_order_message()
                if global_vars.game is not model.game.game.NULL_GAME:
                    game_utils.backup("current_game.pckl")

        except asyncio.TimeoutError:
            await message_utils.safe_send(message.author, "Timed out. Hand status not changed.")
        except Exception as e:
            # log but avoid importing logger here; bot_impl logs to bot_client.logger
            bot_client.logger.error(f"Error during hand status prompt for ST in presetvote: {e}")
        return

    # Player path
    the_player = player_utils.get_player(message.author)
    if not the_player:
        await message_utils.safe_send(message.author, "You are not in the game.")
        return

    player_banshee_ability = character_utils.the_ability(the_player.character, model.characters.Banshee)
    banshee_override = player_banshee_ability and player_banshee_ability.is_screaming

    if argument in ["0", "1", "2"]:
        if not banshee_override:
            await message_utils.safe_send(message.author,
                                          f"{argument} is not a valid vote. Use 'yes', 'y', 'no', or 'n'.")
            return
        vt = int(argument)
    else:
        vt = int(argument == "yes" or argument == "y")

    if voudon_in_play and the_player != voudon_in_play and not the_player.is_ghost and vt > 0:
        await message_utils.safe_send(message.author,
                                      "Voudon is in play. Only the Voudon and dead may vote. Wait to see if you die before voting yes.")
        return

    await vote.preset_vote(the_player, vt)
    await message_utils.safe_send(message.author,
                                  "Successfully preset! For more nuanced presets, contact the storytellers.")
    if global_vars.game is not model.game.game.NULL_GAME:
        game_utils.backup("current_game.pckl")

    # Prompt for hand status
    try:
        hand_status_prompt = await message_utils.safe_send(message.author,
                                                           "Hand up or down? (up/down/cancel)")
        hand_status_choice = await bot_client.client.wait_for(
            "message",
            check=(lambda x: x.author == message.author and x.channel == hand_status_prompt.channel),
            timeout=200,  # 200 seconds to respond
        )
        choice_content = hand_status_choice.content.lower()
        if choice_content == "up":
            the_player.hand_raised = True
            await message_utils.safe_send(message.author, "Your hand is now up.")
        elif choice_content == "down":
            the_player.hand_raised = False
            await message_utils.safe_send(message.author, "Your hand is now down.")
        elif choice_content == "cancel":
            await message_utils.safe_send(message.author, "Hand status change cancelled.")
        else:
            await message_utils.safe_send(message.author, "Invalid choice. Hand status not changed.")

        if choice_content in ["up", "down"]:
            await global_vars.game.update_seating_order_message()
            if global_vars.game is not model.game.game.NULL_GAME:
                game_utils.backup("current_game.pckl")

    except asyncio.TimeoutError:
        await message_utils.safe_send(message.author, "Timed out. Hand status not changed.")
    except Exception as e:
        bot_client.logger.error(f"Error during hand status prompt after presetvote: {e}")
    return


@registry.command(
    name="cancelprevote",
    description="cancels an existing prevote",
    aliases=["cancelpreset"],
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER, UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=True
)
async def cancelprevote_command(message: discord.Message, argument: str):
    """Cancel preset vote for yourself (player) or anyone (storyteller)."""
    # Ported from bot_impl.py cancelpreset handling
    bot_client.logger.info("cancelprevote_command invoked by %s", getattr(message.author, 'id', None))
    if global_vars.game is model.game.game.NULL_GAME:
        await message_utils.safe_send(message.author, "There's no game right now.")
        return

    if global_vars.game.isDay == False:
        await message_utils.safe_send(message.author, "It's not day right now.")
        return

    if global_vars.game.days[-1].votes == [] or global_vars.game.days[-1].votes[-1].done == True:
        await message_utils.safe_send(message.author, "There's no vote right now.")
        return

    vote = global_vars.game.days[-1].votes[-1]
    bot_client.logger.info("Current presetVotes before cancel: %s", vote.presetVotes)

    # Storyteller path
    if global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
        msg = await message_utils.safe_send(message.author, "Whose vote do you want to cancel?")
        try:
            reply = await bot_client.client.wait_for(
                "message",
                check=(lambda x: x.author == message.author and x.channel == msg.channel),
                timeout=200,
            )
        except asyncio.TimeoutError:
            await message_utils.safe_send(message.author, "Timed out.")
            return

        if reply.content.lower() == "cancel":
            await message_utils.safe_send(message.author, "Cancelling preset cancelled!")
            return

        reply_text = reply.content.lower()
        person = await player_utils.select_player(
            message.author, reply_text, global_vars.game.seatingOrder
        )
        if person is None:
            return

        await vote.cancel_preset(person)
        bot_client.logger.info("Current presetVotes after cancel (ST path): %s", vote.presetVotes)
        await message_utils.safe_send(message.author, "Successfully canceled!")
        if global_vars.game is not model.game.game.NULL_GAME:
            game_utils.backup("current_game.pckl")

        # Prompt for hand status (Storyteller context)
        try:
            hand_status_prompt_st = await message_utils.safe_send(message.author,
                                                                  f"Hand up or down for {person.display_name}? (up/down/cancel)")
            hand_status_choice_st = await bot_client.client.wait_for(
                "message",
                check=(lambda x: x.author == message.author and x.channel == hand_status_prompt_st.channel),
                timeout=200,
            )
            choice_content_st = hand_status_choice_st.content.lower()
            if choice_content_st == "up":
                person.hand_raised = True
                await message_utils.safe_send(message.author, f"{person.display_name}'s hand is now up.")
            elif choice_content_st == "down":
                person.hand_raised = False
                await message_utils.safe_send(message.author, f"{person.display_name}'s hand is now down.")
            elif choice_content_st == "cancel":
                await message_utils.safe_send(message.author, "Hand status change cancelled.")
            else:
                await message_utils.safe_send(message.author, "Invalid choice. Hand status not changed.")

            if choice_content_st in ["up", "down"]:
                await global_vars.game.update_seating_order_message()
                if global_vars.game is not model.game.game.NULL_GAME:
                    game_utils.backup("current_game.pckl")

        except asyncio.TimeoutError:
            await message_utils.safe_send(message.author, "Timed out. Hand status not changed.")
        except Exception as e:
            bot_client.logger.error(f"Error during hand status prompt for ST in cancelpreset: {e}")
        return

    # Player path
    the_player = player_utils.get_player(message.author)
    if not the_player:
        await message_utils.safe_send(message.author, "You are not in the game.")
        return

    await vote.cancel_preset(the_player)
    bot_client.logger.info("Current presetVotes after cancel (player path): %s", vote.presetVotes)
    await message_utils.safe_send(message.author,
                                  "Successfully canceled! For more nuanced presets, contact the storytellers.")
    if global_vars.game is not model.game.game.NULL_GAME:
        game_utils.backup("current_game.pckl")

    # Prompt for hand status
    try:
        hand_status_prompt = await message_utils.safe_send(message.author,
                                                           "Hand up or down? (up/down/cancel)")
        hand_status_choice = await bot_client.client.wait_for(
            "message",
            check=(lambda x: x.author == message.author and x.channel == hand_status_prompt.channel),
            timeout=200,  # 200 seconds to respond
        )
        choice_content = hand_status_choice.content.lower()
        if choice_content == "up":
            the_player.hand_raised = True
            await message_utils.safe_send(message.author, "Your hand is now up.")
        elif choice_content == "down":
            the_player.hand_raised = False
            await message_utils.safe_send(message.author, "Your hand is now down.")
        elif choice_content == "cancel":
            await message_utils.safe_send(message.author, "Hand status change cancelled.")
        else:
            await message_utils.safe_send(message.author, "Invalid choice. Hand status not changed.")

        if choice_content in ["up", "down"]:
            await global_vars.game.update_seating_order_message()
            if global_vars.game is not model.game.game.NULL_GAME:
                game_utils.backup("current_game.pckl")

    except asyncio.TimeoutError:
        await message_utils.safe_send(message.author, "Timed out. Hand status not changed.")
    except Exception as e:
        bot_client.logger.error(f"Error during hand status prompt after cancelpreset: {e}")
    return


@registry.command(
    name="defaultvote",
    description="will always vote vote in time minutes. if no arguments given, deletes existing defaults.",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER],
    arguments=[CommandArgument("vote=no", optional=True), CommandArgument("time=60", optional=True)],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def defaultvote_command(message: discord.Message, argument: str):
    """Set/remove default vote and optional duration."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="adjustvotes",
    description="Amnesiac multiplies another player's vote",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("amnesiac"), CommandArgument("target"), CommandArgument("multiplier")],
    required_phases=[GamePhase.DAY],  # Day only
    aliases=["adjustvote"],
    implemented=False
)
async def adjustvotes_command(message: discord.Message, argument: str):
    """Amnesiac multiplies another player's vote."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="nominate",
    description="nominates player",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER, UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def nominate_command(message: discord.Message, argument: str):
    """Nominate another player for execution."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")
