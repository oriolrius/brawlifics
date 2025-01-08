import random
from typing import Optional
from pydantic import BaseModel
from brawlifics.lib.config import config
from brawlifics.lib.utils import safe_eval
from brawlifics.lib.logger import logger


class Player(BaseModel):
    name: str
    game_id: str = None
    image_path: str = None
    position: float = 0.0
    status: str = "waiting"
    challenge: Optional[str] = None
    _mqtt_client: Optional[object] = None

    def __init__(self, **data):
        super().__init__(**data)

    def move(self, distance: float, track_length: float = config.TRACK_LENGTH) -> None:
        """Move the player forward on the track."""
        self.position = min(self.position + distance, track_length)
        logger.info(
            f"[player] Moved, current: {self.position}/{track_length} <- [game/player] [{self.game_id}/{self.name}]"
        )
        if self.position >= track_length:
            logger.info(
                f"[player] FINISHED, current: {self.position}/{track_length} <- [game/player] [{self.game_id}/{self.name}]"
            )
            self.status = "finished"

    def new_challenge(self) -> str:
        """Generate a new challenge for this player."""
        operations = ['+', '-', '*']
        operation = random.choice(operations)

        if operation in ['+', '-']:
            a = random.randint(1, 99)
            b = random.randint(1, 99)
            if operation == '-' and a < b:
                a, b = b, a
        else:
            a = random.randint(1, 10)
            b = random.randint(1, 10)

        self.challenge = f"{a} {operation} {b}"
        if not self._mqtt_client:
            logger.error(f"No MQTT client available for player {self.name}")
        else:
            self._mqtt_client.publish(
                config.CHALLENGE_TOPIC.format(self.game_id, self.name), self.challenge
            )
        self.status = "challenged"
        return self.challenge

    def check_challenge(self, answer: str) -> bool:
        """Verify if the answer matches the current challenge."""
        logger.info(
            f"[player] Checking challenge: {self.challenge} == answer: {answer} <- [game/player] [{self.game_id}/{self.name}]"
        )
        if not self.challenge:
            logger.debug(f"Player {self.name} has no active challenge")
            return False

        try:
            if int(answer) == safe_eval(self.challenge):
                logger.info(
                    f"[player] Challenge {self.challenge}: OK <- [game/player] [{self.game_id}/{self.name}]"
                )
                self.status = "waiting"
                self.challenge = None
                return True
            else:
                logger.info(
                    f"[player] Challenge {self.challenge}: FAIL <- [game/player] [{self.game_id}/{self.name}]"
                )
                return False
        except Exception as e:
            logger.error(f"Error checking challenge: {e}")
            return False
