import pytest
import httpx
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import time
from typing import List
from brawlifics.lib.utils import safe_eval
from tests.utils import step
from brawlifics.lib.config import config
import logging
import asyncio
import pytest_asyncio
import random
import string

logger = logging.getLogger(__name__)

class TestPlayerJourney:
    # Test configuration
    #BASE_URL = f"http://{config.HOST}:{config.PORT}"
    BASE_URL = "http://localhost:8000"
    MQTT_BROKER = "localhost"
    MQTT_PORT = config.MQTT_WS_PORT
    MQTT_TOPIC_BASE = config.MQTT_TOPIC_BASE
    MQTT_CHALLENGE_TOPIC = config.CHALLENGE_TOPIC
    MQTT_RESULT_TOPIC = config.RESULT_TOPIC
    MQTT_GAME_STATUS_TOPIC = config.GAME_STATUS_TOPIC
    MQTT_GAME_WINNER_TOPIC = config.GAME_WINNER_TOPIC

    async def publish_result(self, game_id: str, player_name: str, result: str):
        topic = self.MQTT_RESULT_TOPIC.format(game_id, player_name)
        self.mqtt_client.publish(topic, result)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        assert reason_code == 0, "Failed to connect to MQTT broker"
        
    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        logger.debug(f"Received message: {payload} on topic: {msg.topic}")
        if msg.topic.endswith("/challenge"):
            self.received_challenges.append((msg.topic, payload))
        if msg.topic.endswith("/status"):
            self.game_status = payload
        if msg.topic.endswith("/winner"):
            self.game_winner = payload

    @pytest_asyncio.fixture
    async def mqtt_client(self):
        """Create and configure MQTT client fixture."""
        self.mqtt_client = mqtt.Client(
            client_id=''.join(random.choices(string.ascii_letters + string.digits, k=8)),
            transport="websockets",
            protocol=mqtt.MQTTv5,
            callback_api_version=CallbackAPIVersion.VERSION2
            )

        # Store received messages
        self.received_challenges = []
        self.challenge = None
        self.game_status = 'playing'

        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        # Connect to broker
        self.mqtt_client.connect(self.MQTT_BROKER, self.MQTT_PORT)
        self.mqtt_client.loop_start()
        
        yield self.mqtt_client
        
        # Cleanup
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
    
    @pytest.fixture
    def http_client(self):
        """Create HTTP client fixture."""
        with httpx.Client(base_url=self.BASE_URL) as client:
            yield client

    @pytest.mark.asyncio
    async def test_complete_player_journey(self, http_client: httpx.Client, mqtt_client: mqtt.Client):
        """Test the complete journey of a player"""
        players_names = ["test_player_1", "test_player_2", "test_player_3", "test_player_4", "test_player_5", "test_player_6"]
        #players_names = ["test_player_1", "test_player_2"]
        
        def create_game():
            response = http_client.post("/api/game", json={"game_id": None})
            assert response.status_code == 200, "Failed to create game"
            game_data = response.json()
            assert game_data["game_id"] is not None
            return game_data["game_id"]
        
        def register_players(game_id: str, players_names: List[str]):
            # Randomize player registration order
            shuffled_players = players_names.copy()
            random.shuffle(shuffled_players)
            
            for player_name in shuffled_players:
                logger.info(f"Registering player {player_name} for game {game_id}")
                response = http_client.post("/api/players", json={
                    "name": player_name,
                    "game_id": game_id,
                    "image_path": "Character"
                })
                assert response.status_code == 200
                game_data = response.json()
                assert game_data["players"][player_name]["name"] == player_name
                logger.info(f"Player {player_name} registered for game {game_id}")
        
        def verify_players_in_game(game_id: str, players_names: List[str]):
            for player_name in players_names:
                response = http_client.get(f"/api/game/{game_id}")
                assert response.status_code == 200, "Failed to get game status"
                game_data = response.json()
                assert player_name in game_data["players"], f"Player {player_name} not found in game players list"
        
        def setup_mqtt(game_id: str):
            mqtt_client.subscribe(self.MQTT_CHALLENGE_TOPIC.format(game_id, '+'))
            mqtt_client.subscribe(self.MQTT_GAME_STATUS_TOPIC.format(game_id))
            mqtt_client.subscribe(self.MQTT_GAME_WINNER_TOPIC.format(game_id))

        def start_game(game_id: str):
            response = http_client.post(f"/api/game/{game_id}")
            assert response.status_code == 200, "Failed to start game"

        # Execute the steps
        game_id = step("Create game", create_game)
        logger.info(f"Game: {game_id}")
        step("Register player", register_players(game_id, players_names))
        step("Verify player in game", verify_players_in_game(game_id, players_names))
        step("Setup MQTT", setup_mqtt(game_id))
        step("Start game", start_game(game_id))
        # Start the challenge processing in the background
        await self.process_challenges()
        await asyncio.sleep(1)
        step("Verify game winner", self.verify_game_winner(game_id, players_names))

    def verify_game_winner(self, game_id: str, players_names: List[str]):
        logger.info(f"[Game: {game_id}] ** The winner is {self.game_winner} **")
        assert self.game_winner in players_names, f"Game winner {self.game_winner} not in players names"

    async def process_challenges(self):
        while self.game_status == 'playing':
            logger.info(f"Game status: {self.game_status} - waiting for game to finish")
            try:
                msg = self.received_challenges.pop()
                topic = msg[0]
                challenge = msg[1]
                # topic exmample: brawlifics/game/135/player/test_player/challenge
                game_id = topic.split('/')[-4]
                player_name = topic.split('/')[-2]
                logger.info(f"Challenge: {challenge} - [{game_id}/{player_name}]")
                result = safe_eval(challenge)
                logger.info(f"Result published: {result} <- [{game_id}/{player_name}]")
                await self.publish_result(game_id, player_name, result)
            except IndexError:
                logger.info("No messages received yet")
                await asyncio.sleep(5)
