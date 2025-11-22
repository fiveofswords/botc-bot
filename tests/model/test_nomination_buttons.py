import pytest
from unittest.mock import AsyncMock, MagicMock

# Import fixtures so pytest registers them
from tests.fixtures.discord_mocks import mock_discord_setup  # noqa: F401
from tests.fixtures.game_fixtures import setup_test_game  # noqa: F401


@pytest.mark.asyncio
async def test_initialization_buttons(mock_discord_setup, setup_test_game):
    """NominationButtonsView initializes with prevote and hand buttons."""
    # Use helper import
    nb, _ = _import_nb_and_Vote()

    alice_member = mock_discord_setup['members']['alice']

    view = _make_view(nb, "Nominee", "Nominator", alice_member)

    labels = [item.label for item in view.children]

    assert "Prevote Yes" in labels
    assert "Prevote No" in labels
    assert any(l in ("Raise Hand", "Lower Hand") for l in labels)


@pytest.mark.asyncio
async def test_send_nomination_buttons_to_st_channels(mock_discord_setup, setup_test_game, monkeypatch):
    """send_nomination_buttons_to_st_channels sends messages and tracks them."""
    nb, Vote = _import_nb_and_Vote()
    game = setup_test_game['game']
    players = setup_test_game['players']

    # Ensure day/vote state (use helper)
    game.isDay = True
    _ensure_active_vote(game, players, 'alice', 'storyteller')

    _patch_settings_and_safe_send(monkeypatch, game, mock_discord_setup)

    # Clear any existing state
    nb._active_nomination_messages.clear()

    await nb.send_nomination_buttons_to_st_channels("Nominee", "Nominator", 3)

    # All seatingOrder players should have messages tracked
    assert len(nb._active_nomination_messages) == len(game.seatingOrder)

    for p in game.seatingOrder:
        assert p.user.id in nb._active_nomination_messages
        message, view = nb._active_nomination_messages[p.user.id]
        assert hasattr(message, 'content')
        assert isinstance(view, nb.NominationButtonsView)


@pytest.mark.asyncio
async def test_handle_prevote_sets_preset(mock_discord_setup, setup_test_game):
    """_handle_prevote should set current_vote.presetVotes and call update_seating_order_message."""
    nb, Vote = _import_nb_and_Vote()
    game = setup_test_game['game']
    players = setup_test_game['players']

    game.isDay = True
    _ensure_active_vote(game, players, 'bob', 'storyteller')

    alice_member = mock_discord_setup['members']['alice']
    view = _make_view(nb, "Bob", "Storyteller", alice_member)

    interaction = _make_interaction(alice_member)

    # Patch update_seating_order_message to verify it's called
    update_seating_order_message = _patch_update_seating_message(game)

    await view._handle_prevote(interaction, "yes")

    current_vote = game.days[-1].votes[-1]
    assert current_vote.presetVotes[alice_member.id] == 1
    interaction.response.send_message.assert_awaited()
    update_seating_order_message.assert_awaited()


@pytest.mark.asyncio
async def test_handle_vote_calls_vote_method(mock_discord_setup, setup_test_game):
    """_handle_vote should acknowledge, disable buttons and call Vote.vote."""
    nb, Vote = _import_nb_and_Vote()
    game = setup_test_game['game']
    players = setup_test_game['players']

    game.isDay = True
    # use helper to create vote and patch its vote method
    vote = _ensure_active_vote(game, players, 'charlie', 'storyteller')
    vote.vote = AsyncMock()

    bob_member = mock_discord_setup['members']['bob']
    view = _make_view(nb, "Charlie", "Storyteller", bob_member)

    # Attach a message so edits are safe
    await _attach_message(view, mock_discord_setup['channels']['st_bob'])

    interaction = _make_interaction(bob_member)

    # Put the view into voting-turn mode
    view.update_for_voting_turn()

    await view._handle_vote(interaction, 1)

    interaction.response.send_message.assert_awaited()
    vote.vote.assert_awaited_with(1, voter=players['bob'])


@pytest.mark.asyncio
async def test_handle_cancel_prevote_removes_preset(mock_discord_setup, setup_test_game):
    """_handle_cancel_prevote should remove preset vote and update seating message."""
    nb, Vote = _import_nb_and_Vote()
    game = setup_test_game['game']
    players = setup_test_game['players']

    game.isDay = True
    vote = _ensure_active_vote(game, players, 'bob', 'storyteller')
    # preset Alice's vote
    alice_id = mock_discord_setup['members']['alice'].id
    vote.presetVotes[alice_id] = 1

    alice_member = mock_discord_setup['members']['alice']
    view = _make_view(nb, "Bob", "Storyteller", alice_member)

    interaction = _make_interaction(alice_member)

    # Patch update_seating_order_message to verify it's called
    update_seating_order_message = _patch_update_seating_message(game)

    await view._handle_cancel_prevote(interaction)

    current_vote = game.days[-1].votes[-1]
    assert alice_id not in current_vote.presetVotes
    interaction.response.send_message.assert_awaited()
    update_seating_order_message.assert_awaited()


@pytest.mark.asyncio
async def test_handle_hand_toggle_raise(mock_discord_setup, setup_test_game):
    """_handle_hand_toggle should raise hand and update seating message."""
    nb, Vote = _import_nb_and_Vote()
    game = setup_test_game['game']
    players = setup_test_game['players']

    game.isDay = True
    _ensure_active_vote(game, players, 'bob', 'storyteller')

    alice_member = mock_discord_setup['members']['alice']
    alice_player = players['alice']
    alice_player.hand_raised = False

    view = _make_view(nb, "Bob", "Storyteller", alice_member)
    # attach a message so edits don't fail
    await _attach_message(view, mock_discord_setup['channels']['st_alice'])

    interaction = _make_interaction(alice_member)

    # Patch update_seating_order_message to verify it's called
    update_seating_order_message = _patch_update_seating_message(game)

    # Raise hand
    await view._handle_hand_toggle(interaction)
    assert alice_player.hand_raised is True
    interaction.response.send_message.assert_awaited()
    update_seating_order_message.assert_awaited()


@pytest.mark.asyncio
async def test_handle_hand_toggle_lower(mock_discord_setup, setup_test_game):
    """_handle_hand_toggle should lower hand and update seating message."""
    nb, Vote = _import_nb_and_Vote()
    game = setup_test_game['game']
    players = setup_test_game['players']

    game.isDay = True
    _ensure_active_vote(game, players, 'bob', 'storyteller')

    alice_member = mock_discord_setup['members']['alice']
    alice_player = players['alice']
    alice_player.hand_raised = True

    view = _make_view(nb, "Bob", "Storyteller", alice_member)
    # attach a message so edits don't fail
    await _attach_message(view, mock_discord_setup['channels']['st_alice'])

    interaction = _make_interaction(alice_member)

    # Patch update_seating_order_message to verify it's called
    update_seating_order_message = _patch_update_seating_message(game)

    # Lower hand
    await view._handle_hand_toggle(interaction)
    assert alice_player.hand_raised is False
    interaction.response.send_message.assert_awaited()
    update_seating_order_message.assert_awaited()


@pytest.mark.asyncio
async def test_handle_hand_toggle_locked_hand(mock_discord_setup, setup_test_game):
    """If a player's hand is locked for vote, toggling should be blocked."""
    import model.nomination_buttons as nb

    game = setup_test_game['game']
    players = setup_test_game['players']

    game.isDay = True
    _ensure_active_vote(game, players, 'bob', 'storyteller')

    alice_member = mock_discord_setup['members']['alice']
    alice_player = players['alice']
    alice_player.hand_locked_for_vote = True

    view = _make_view(nb, "Bob", "Storyteller", alice_member)

    interaction = _make_interaction(alice_member)

    await view._handle_hand_toggle(interaction)

    # Hand state should not change and a locked message should be sent
    assert alice_player.hand_locked_for_vote is True
    interaction.response.send_message.assert_awaited()


@pytest.mark.asyncio
async def test_update_enable_disable_clear_nomination_messages(mock_discord_setup, setup_test_game, monkeypatch):
    """Verify update/enable/disable/clear flows for nomination messages."""
    import model.nomination_buttons as nb
    game = setup_test_game['game']
    players = setup_test_game['players']

    # Make sure there's an active vote so messages are sent
    game.isDay = True
    _ensure_active_vote(game, players, 'alice', 'storyteller')

    _patch_settings_and_safe_send(monkeypatch, game, mock_discord_setup)

    # Clear any existing state and send buttons
    nb._active_nomination_messages.clear()
    await nb.send_nomination_buttons_to_st_channels("Nominee", "Nominator", 3)

    _patch_message_edit_on_tracked(nb)

    # Pick a player (alice) and update their buttons to voting turn
    alice_id = players['alice'].user.id
    assert alice_id in nb._active_nomination_messages

    # Update to voting turn
    await nb.update_buttons_for_voting_turn(alice_id)
    message, view = nb._active_nomination_messages[alice_id]
    # The message should now mention the player's display name (it's their turn)
    assert players['alice'].display_name in message.content

    # Re-enable buttons (after vote)
    await nb.enable_buttons_for_voter(alice_id)
    message_after_enable, view_after = nb._active_nomination_messages[alice_id]
    assert "Please set a prevote" in message_after_enable.content

    # Clear all nomination messages
    await nb.clear_nomination_messages()
    assert len(nb._active_nomination_messages) == 0


# Helper utilities to reduce duplication in tests
def _import_nb_and_Vote():
    import model.nomination_buttons as nb
    from model.game.vote import Vote
    return nb, Vote


def _ensure_active_vote(game, players, nominee_key='alice', nominator_key='storyteller'):
    from model.game.vote import Vote
    vote = Vote(players[nominee_key], players[nominator_key])
    game.days[-1].votes.append(vote)
    return vote


def _make_interaction(member):
    interaction = MagicMock()
    interaction.user = member
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def _patch_settings_and_safe_send(monkeypatch, game, mock_discord_setup):
    class DummySettings:
        @staticmethod
        def load():
            return DummySettings()

        def get_st_channel(self, user_id):
            for p in game.seatingOrder:
                if p.user.id == user_id:
                    return p.st_channel.id if p.st_channel else None
            return None

    monkeypatch.setattr('model.settings.GameSettings.load', DummySettings.load)
    monkeypatch.setattr('bot_client.client', mock_discord_setup['client'])

    async def fake_safe_send(channel, content, view=None):
        return await channel.send(content=content)

    monkeypatch.setattr('utils.message_utils.safe_send', fake_safe_send)


def _patch_message_edit_on_tracked(nb):
    # Ensure tracked messages accept message.edit(view=...)
    for pid, (msg, vw) in list(nb._active_nomination_messages.items()):
        async def _edit(m=msg, **kwargs):
            if 'content' in kwargs and kwargs['content'] is not None:
                m.content = kwargs['content']
            return m

        msg.edit = _edit


def _patch_update_seating_message(game):
    game.update_seating_order_message = AsyncMock()
    return game.update_seating_order_message


def _make_view(nb, nominee_name, nominator_name, member):
    return nb.NominationButtonsView(nominee_name, nominator_name, 3, member.id)


async def _attach_message(view, channel):
    msg = await channel.send("initial")
    view.message = msg
    return msg
