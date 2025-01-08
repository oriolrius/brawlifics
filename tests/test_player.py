#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from brawlifics.lib.player import Player
from brawlifics.lib.config import config

class TestPlayer:
    @pytest.fixture
    def player1(self):
        return Player(
            name="Player 1",
            game_id="game1",
            image_path="Character 1"
        )

    def test_player_initialization(self, player1):
        assert player1.name == "Player 1"
        assert player1.game_id == "game1"
        assert player1.image_path == "Character 1"

    def test_move(self, player1):
        player1.move(
            distance=config.TRACK_LENGTH / 10
        )
        assert player1.position == (config.TRACK_LENGTH / 10)
        assert player1.status != "finished"

    def test_move_to_the_end(self, player1):
        player1.move(
            distance=config.TRACK_LENGTH
        )
        assert player1.position == config.TRACK_LENGTH
        assert player1.status == "finished"

if __name__ == "__main__":
    pytest.main()
