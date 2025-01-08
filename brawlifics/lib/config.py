import os
import json
from pathlib import Path
from typing import Union
from dotenv import load_dotenv
from brawlifics.lib.logger import logger

# Load environment variables from .env file
load_dotenv()

class Config:
    def _get_value(self, key: str, default: Union[str, int, float, bool]) -> Union[str, int, float, bool]:
        value = os.getenv(key, default)
        logger.debug(f"Config: {key} = {value} (default: {default})")
        if isinstance(default, bool):
            return value.lower() == "true"
        return type(default)(value)

    def __init__(self):
        # Server settings
        self.HTTP_SECURE: bool = self._get_value('HTTP_SECURE', "False")
        self.HOST: str = self._get_value('HOST', "localhost")
        self.PORT: int = int(self._get_value('PORT', "8000"))
        self.DEBUG: bool = self._get_value('DEBUG', "True")
        self.RELOAD: bool = self._get_value('RELOAD', "True")
        
        # MQTT settings
        self.MQTT_SECURE: bool = self._get_value('MQTT_SECURE', "False")
        self.MQTT_BROKER: str = self._get_value('MQTT_BROKER', "localhost")
        self.MQTT_PORT: int = int(self._get_value('MQTT_PORT', "1883"))
        self.MQTT_WS_PORT: int = int(self._get_value('MQTT_WS_PORT', "9001"))
        self.MQTT_URI: str = self._get_value('MQTT_URI', "mqtt")
        self.MQTT_URL: str = self.get_mqtt_url()
        self.MQTT_FE_USER: str = self._get_value('MQTT_FE_USER', "frontend")
        self.MQTT_FE_PASS: str = self._get_value('MQTT_FE_PASS', "The2password.")
        self.MQTT_BO_USER: str = self._get_value('MQTT_BO_USER', "backoffice")
        self.MQTT_BO_PASS: str = self._get_value('MQTT_BO_PASS', "The2password.")
        self.MQTT_BE_USER: str = self._get_value('MQTT_BE_USER', "backend")
        self.MQTT_BE_PASS: str = self._get_value('MQTT_BE_PASS', "The2password.")
        logger.debug(f"Config: MQTT_URL = {self.MQTT_URL}")
        
        # Game settings
        self.TRACK_LENGTH: float = float(self._get_value('TRACK_LENGTH', "10.0"))
        self.MAX_PLAYERS: int = int(self._get_value('MAX_PLAYERS', "6"))
        
        # File paths
        self.ASSETS_FOLDER: Path = Path(self._get_value('ASSETS_FOLDER', "assets"))
        self.DATA_FOLDER: Path = Path(self._get_value('DATA_FOLDER', "data"))
        
        # MQTT topics
        self.MQTT_TOPIC_BASE: str = self._get_value('MQTT_TOPIC_BASE', "brawlifics")
        self.CHALLENGE_TOPIC: str = self._get_value('CHALLENGE_TOPIC', f"{self.MQTT_TOPIC_BASE}/game/{{}}/player/{{}}/challenge")
        self.RESULT_TOPIC: str = self._get_value('RESULT_TOPIC', f"{self.MQTT_TOPIC_BASE}/game/{{}}/player/{{}}/result")
        self.PLAYER_TOPIC: str = self._get_value('PLAYER_TOPIC', f"{self.MQTT_TOPIC_BASE}/game/{{}}/player/{{}}")
        self.GAME_STATUS_TOPIC: str = self._get_value('GAME_STATUS_TOPIC', f"{self.MQTT_TOPIC_BASE}/game/{{}}/status")
        self.GAME_WINNER_TOPIC: str = self._get_value('GAME_WINNER_TOPIC', f"{self.MQTT_TOPIC_BASE}/game/{{}}/winner")
        self.GAME_PLAYERS_TOPIC: str = self._get_value('GAME_PLAYERS_TOPIC', f"{self.MQTT_TOPIC_BASE}/game/{{}}/players")

        # Logging settings
        self.LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FORMAT: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def get_mqtt_url(self) -> str:
        part = f"{self.MQTT_BROKER}:{self.MQTT_WS_PORT}/{self.MQTT_URI}"
        if eval(self.MQTT_SECURE):
            return f"wss://{part}"
        return f"ws://{part}"

    def get_dict(self) -> dict:
        # Get all instance attributes that don't start with _
        config_dict = {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("_")
        }

        # Convert Path objects to strings
        for key, value in config_dict.items():
            if isinstance(value, Path):
                config_dict[key] = str(value)

        return config_dict

    def get_json(self) -> str:
        return json.dumps(self.get_dict())


# Create singleton instance
config = Config()
