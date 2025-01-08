#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from brawlifics.lib.config import config
from brawlifics.lib.player import Player
from brawlifics.lib.game import Game 
from brawlifics.lib.server import Server

class TestServer:
    @pytest.fixture
    def server(self):
        """Create a clean server instance for each test"""
        return Server()

    @pytest.fixture
    def game_id(self):
        """Standard game ID for testing"""
        return "game1"

    @pytest.fixture 
    def player(self):
        """Create a test player"""
        return Player(
            name="Player 1",
            game_id="game1",
            image_path="Character 1"
        )

    @pytest.fixture
    def server_with_game(self, server, game_id):
        """Server with a pre-created game"""
        server.create_game(game_id)
        return server

    def test_server_initialization(self, server):
        """Test fresh server initialization"""
        assert server.games == {}
        assert isinstance(server.games, dict)

    def test_create_game(self, server, game_id):
        """Test game creation"""
        game = server.create_game(game_id)
        assert server.games[game_id] == game
        assert isinstance(game, Game)
        assert game.game_id == game_id

    def test_get_game(self, server_with_game, game_id):
        """Test retrieving an existing game"""
        game = server_with_game.get_game(game_id)
        assert isinstance(game, Game)
        assert game.game_id == game_id

    def test_get_nonexistent_game(self, server):
        """Test retrieving a game that doesn't exist"""
        game = server.get_game("nonexistent")
        assert game is None

    def test_start_game(self, server_with_game, game_id):
        """Test starting a game"""
        assert server_with_game.start_game(game_id)
        game = server_with_game.get_game(game_id)
        assert game.status == "playing"

    def test_end_game(self, server_with_game, game_id):
        """Test ending a game"""
        assert server_with_game.end_game(game_id)
        assert server_with_game.get_game(game_id) is None

    def test_add_player(self, server_with_game, game_id, player):
        """Test adding a player to a game"""
        assert server_with_game.add_player(game_id, player) is True
        # game = server_with_game.get_game(game_id)
        # assert game.players[player.name] == player

    def test_add_player_to_nonexistent_game(self, server, player):
        """Test adding a player to a game that doesn't exist"""
        assert not server.add_player("nonexistent", player)

    def test_get_player(self, server_with_game, game_id, player):
        """Test retrieving a player from a game"""
        server_with_game.add_player(game_id, player)
        retrieved_player = server_with_game.get_player(game_id, player.name)
        assert retrieved_player == player

    def test_get_nonexistent_player(self, server_with_game, game_id):
        """Test retrieving a player that doesn't exist"""
        retrieved_player = server_with_game.get_player(game_id, "nonexistent")
        assert retrieved_player is None

if __name__ == "__main__":
    pytest.main()
