from typing import Dict, List, Optional
from pydantic import BaseModel
from brawlifics.lib.game import Game
from brawlifics.lib.player import Player
from brawlifics.lib.logger import logger
from brawlifics.lib.config import config


class Server(BaseModel):
    games: Dict[str, Game] = {}

    def create_game(
        self, game_id: Optional[str] = None, track_length: float = config.TRACK_LENGTH
    ) -> Game:
        game = Game(game_id=game_id, track_length=track_length)
        print(game)
        self.games[game.game_id] = game
        logger.info(f"Game created with ID: {game.game_id}")
        return game

    def get_games(self) -> List[Game]:
        return list(self.games.values())

    def get_game(self, game_id: str) -> Optional[Game]:
        return self.games.get(game_id)

    def start_game(self, game_id: str) -> bool:
        game = self.get_game(game_id)
        if game:
            game.start()
            logger.info(f"Game {game_id} started.")
            return True
        logger.error(f"Game {game_id} not found.")
        return False

    def end_game(self, game_id: str) -> bool:
        game = self.get_game(game_id)
        if game:
            game.end()
            logger.info(f"Game {game_id} ended.")
            self.remove_game(game_id)
            return True
        logger.error(f"Game {game_id} not found.")
        return False

    def add_player(self, game_id: str, player: Player) -> bool:
        game = self.get_game(game_id)
        if game:
            game.add_player(player_name=player.name, image_path=player.image_path)
            logger.info(f"Player {player.name} added to game {game_id}.")
            return True
        logger.error(f"Game {game_id} not found.")
        return False

    def get_player(self, game_id: str, player_name: str) -> Optional[Player]:
        game = self.get_game(game_id)
        if game:
            return game.players.get(player_name)
        logger.error(f"Game {game_id} not found.")
        return None

    def remove_game(self, game_id: str) -> bool:
        if game_id in self.games:
            del self.games[game_id]
            logger.info(f"Game {game_id} removed.")
            return True
        logger.error(f"Game {game_id} not found.")
        return False

    def cleanup_games(self) -> int:
        """Remove finished games."""
        removed = 0
        for game_id in list(self.games.keys()):
            if self.games[game_id].status == "finished":
                del self.games[game_id]
                removed += 1
                logger.info(f"Game {game_id} removed.")
        return removed

    def close_all_games(self) -> int:
        """Close all games."""
        closed = 0
        for game_id in list(self.games.keys()):
            self.end_game(game_id)
            closed += 1
        return closed
