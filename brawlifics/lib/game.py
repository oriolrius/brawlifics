from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from brawlifics.lib.player import Player
from brawlifics.lib.logger import logger
from brawlifics.lib.utils import generate_game_id
from brawlifics.lib.config import config


class Game(BaseModel):
    """
    Represents a game session with multiple players.

    Handles game state, player management, and MQTT communications.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    game_id: Optional[str] = None
    status: str = "waiting"
    players: Dict[str, Player] = Field(default_factory=dict)
    track_length: float = config.TRACK_LENGTH
    _mqtt_client: Optional[object] = None
    _task: Optional[object] = None

    def start(self):
        """Start the game and generate initial challenges for all players."""
        self.status = "playing"
        if self._mqtt_client:
            self._mqtt_client.publish_status(self.status)
            self._mqtt_client.publish_game()

        for player in self.players.values():
            if self._mqtt_client:
                player._mqtt_client = self._mqtt_client
            player.new_challenge()

    def handle_answer(self, player_id: str, answer: str) -> bool:
        """Handle a player's answer to their challenge."""
        logger.info(
            f"[game] Handling answer {answer} <- [game/player] [{self.game_id}/{player_id}]"
        )
        if player_id not in self.players:
            logger.debug(f"Player {player_id} not found")
            return False
        player = self.players[player_id]
        if player.check_challenge(answer) and player.status != "finished":
            player.move(1.0, self.track_length)
            if player.status == "finished":
                self.end()
                self._mqtt_client.publish_winner(self.game_id, player_id)
                self._mqtt_client.publish_game()
                logger.info(f"[game] Game {self.game_id} - status: {self.status}")
            else:
                self._mqtt_client.publish_game()
                player.new_challenge()
            return True
        return False

    def set_mqtt_client(self, mqtt_client: object):
        """Set MQTT client for game and all players."""
        self._mqtt_client = mqtt_client
        # Share the same client with all players
        for player in self.players.values():
            player._mqtt_client = self._mqtt_client

    def get_mqtt_client(self):
        """Get the MQTT client."""
        return self._mqtt_client

    def set_task(self, value):
        """Set the asyncio task."""
        self._task = value

    @field_validator("game_id", mode="before")
    def set_game_id(cls, value):
        """Set game_id to a random value if not provided."""
        return value or generate_game_id()

    def add_player(self, player_name: str, image_path: str) -> None:
        """Add a player to the game and share MQTT client."""
        self.players[player_name] = Player(
            name=player_name, game_id=self.game_id, image_path=image_path
        )
        logger.debug(f"Player added: {self.players[player_name]}")
        # Share MQTT client if we have one
        if self._mqtt_client:
            self.players[player_name]._mqtt_client = self._mqtt_client
            self._mqtt_client.publish_game()

        return self.players[player_name]

    def get_players(self) -> Dict[str, Player]:
        """Get the list of player names."""
        # return list(self.players.values())
        return self.players

    def end(self):
        """End the game."""
        self.status = "finished"
        logger.info(f"[game] Game {self.game_id} - status: {self.status}")
        if self._mqtt_client:
            self._mqtt_client.publish_status(self.status)

    def check_challenge(self, player_id: str, answer: str) -> int:
        if player_id not in self.players:
            logger.debug(f"Player {player_id} not found.")
            return 0.0
