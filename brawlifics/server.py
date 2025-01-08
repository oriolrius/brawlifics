import yaml
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from uvicorn import Config, Server
import asyncio

from brawlifics.lib.routes import router
from brawlifics.lib.server import Server as GameServer
from brawlifics.lib.logger import logger

from brawlifics.lib.config import config


def setup_logging():
    with open("etc/logging.yaml", "r") as f:
        config = yaml.safe_load(f)
    logging.config.dictConfig(config)
    return logging.getLogger("lib")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.logger = setup_logging()
    app.state.logger.debug("Starting server...")
    app.state.server = server
    app.state.config = config
    yield
    if hasattr(app.state, "mqtt_client"):
        await app.state.mqtt_client.disconnect()


app = FastAPI(lifespan=lifespan)
server = GameServer()
logger.debug("Server created.")

# Include routes
app.include_router(router)


async def start_server():
    server_config = Config(
        "server:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_config="etc/logging.yaml",
        log_level=config.LOG_LEVEL,
    )
    server = Server(server_config)
    await server.serve()


async def main():
    server_task = asyncio.create_task(start_server())
    await server_task


if __name__ == "__main__":
    asyncio.run(main())
