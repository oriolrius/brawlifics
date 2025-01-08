#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# how to run: python3 -m pytest test_server.py
from typing import Dict
import pytest
from brawlifics.lib.game import Game
from brawlifics.lib.player import Player

class TestGame:
    @pytest.fixture
    def game1(self):
        return Game(
            game_id="game1"
        )

    @pytest.fixture
    def player1(self):
        return Player(
            name="Player 1",
            game_id="game1",
            image_path="Character 1"
        )

    @pytest.fixture
    def game1_with_player(self, game1, player1):
        game1.add_player(
            player_name=player1.name,
            image_path=player1.image_path
        )
        return game1

    def test_game_initialization(self, game1):
        assert game1.game_id == "game1"
        assert game1.players == {}
        assert isinstance(game1.game_id, str)
        assert game1.status == "waiting"

    def test_game_add_player(self, game1_with_player, player1):
        assert len(game1_with_player.players) == 1
        assert game1_with_player.players[player1.name] == player1

    def test_get_players(self, game1_with_player, player1):
        # Then test getting players
        players = game1_with_player.get_players()
        assert isinstance(players, dict)
        assert player1.name in players
        assert players[player1.name] == player1

    def test_start_game(self, game1_with_player):
        game1_with_player.start()
        assert game1_with_player.status == "playing"

    def test_end_game(self, game1_with_player):
        game1_with_player.end()
        assert game1_with_player.status == "finished"

    def test_player_challenge(self, game1_with_player, player1):
        # Test challenge generation
        player = game1_with_player.players[player1.name]
        challenge = player.new_challenge()
        assert player.challenge is not None
        # Test incorrect answer
        bad_answer = "bad_answer"
        assert player.check_challenge(bad_answer) is False
        # Test correct answer
        good_answer = str(eval(challenge))  # Only for testing!
        assert player.check_challenge(good_answer) is True

if __name__ == "__main__":
    pytest.main()
