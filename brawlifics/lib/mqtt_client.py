import paho.mqtt.client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion
from brawlifics.lib.logger import logger
from brawlifics.lib.config import config


class AsyncMqttClient:
    def __init__(self, broker=None, port=None, game=None, topic=None):
        self.broker = broker or config.MQTT_BROKER
        self.port = port or config.MQTT_PORT
        self.game = game
        self.client_id = game.game_id
        self.topic = topic.format(game.game_id, "+")
        self.client = mqtt_client.Client(
            client_id=self.client_id,
            protocol=mqtt_client.MQTTv5,
            callback_api_version=CallbackAPIVersion.VERSION2,
        )
        self.client.username_pw_set(
            config.MQTT_BE_USER, 
            config.MQTT_BE_PASS
        )
        self.client.enable_logger()
        self._setup_callbacks()

    def _setup_callbacks(self):
        """Setup default callbacks"""
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_log = self.on_log

    def on_log(self, _client, userdata, level, buf):
        """Log MQTT messages, only show INFO and above"""
        if level >= mqtt_client.MQTT_LOG_INFO:
            logger.info(f"[mqtt_client/on_log] Game {self.client_id} - {buf}")

    def handle_message(self, topic: str, payload: str):
        """Handle incoming MQTT messages"""
        logger.info(
            f"[mqtt_client/handle_message] Game {self.client_id} - Topic: {topic} - Payload: {payload}"
        )
        if topic.endswith("/result"):
            player_id = self._extract_player_id(topic)
            if self.game.game_id and player_id and self.game.status == "playing":
                self.game.handle_answer(player_id, payload)

    def _extract_player_id(self, topic: str) -> str:
        """Extract player ID from topic string"""
        # Implement based on your topic structure
        parts = topic.split("/")
        player_id = parts[-2] if len(parts) >= 2 else None
        logger.debug(
            f"[mqtt_client/_extract_player_id] Game {self.client_id} - Player ID: {player_id}"
        )
        return player_id

    def on_message(self, client, userdata, msg):
        """Process incoming messages"""
        payload = msg.payload.decode()
        self.handle_message(msg.topic, payload)
        logger.info(
            f"[mqtt_client] Game {self.client_id}: Received message on topic {msg.topic}"
        )

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info(f"Game {self.client_id}: Connected successfully to the broker.")
            client.subscribe(self.topic)
        else:
            logger.error(f"Game {self.client_id}: Failed to connect with code {rc}.")

    def on_disconnect(self, client, userdata, rc, properties=None, reason=None):
        if rc != 0:
            logger.warning(
                f"Game {self.client_id}: Unexpected disconnection, return code {rc}"
            )

    async def connect(self):
        """Connect to the MQTT broker asynchronously"""
        self.client.connect_async(self.broker, self.port)
        self.client.loop_start()

    async def disconnect(self):
        """Disconnect from the MQTT broker"""
        self.client.disconnect()
        self.client.loop_stop()

    def publish(self, topic, payload, retain=False):
        """Publish a message to a specific topic"""
        self.client.publish(topic, payload, retain=retain)

    def subscribe(self, topic=None):
        """Subscribe to a topic, defaults to self.topic if none provided"""
        topic = topic or self.topic
        self.client.subscribe(topic)

    def publish_status(self, status: str):
        """Publish the game status to the game status topic"""
        self.publish(
            config.GAME_STATUS_TOPIC.format(self.game.game_id), status, retain=False
        )

    def publish_winner(self, game_id: str, player_id: str):
        """Publish the game winner to the game winner topic"""
        self.publish(
            config.GAME_WINNER_TOPIC.format(self.game.game_id), player_id, retain=False
        )

    def publish_game(self):
        """Publish the list of players to the game players topic"""
        # logger.debug(f"[mqtt_client/publish_game] Game {self.game}")
        self.publish(
            config.GAME_PLAYERS_TOPIC.format(self.game.game_id),
            self.game.model_dump_json(),
            retain=False,
        )
