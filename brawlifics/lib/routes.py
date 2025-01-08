import os
import asyncio
from typing import Optional, Dict, List
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, Response, JSONResponse
from fastapi import Depends, Request
from pydantic import BaseModel
import tomli
from brawlifics.lib.logger import logger
from brawlifics.lib.server import Server
from brawlifics.lib.mqtt_client import AsyncMqttClient
from brawlifics.lib.utils import get_first_frame

router = APIRouter()


async def get_server(request: Request):
    return request.app.state.server


async def get_config(request: Request):
    return request.app.state.config


async def run_game(game_id: str, server: Server):
    logger.debug(f"proces: run_game, [game_id: {game_id}]")
    while server.get_game(game_id).status == "playing":
        # iterate over players and check if they have a challenge
        for player in server.get_game(game_id).players.values():
            if player.status == "waiting":
                player.new_challenge()

        await asyncio.sleep(0.1)
    logger.info(f"Game {game_id} finished, exiting task 'run_game'")
    return True


# Models for request/response
class PlayerCreateRequest(BaseModel):
    name: str
    game_id: str
    image_path: str


class PlayerResponse(BaseModel):
    name: str
    game_id: str
    image_path: str
    position: float
    status: str
    challenge: Optional[str] = None


class GameCreateRequest(BaseModel):
    game_id: Optional[str] = None


class GameResponse(BaseModel):
    game_id: str
    status: str
    track_length: float
    players: Dict[str, PlayerResponse]


@router.get("/api/version")
async def get_version():
    with open("pyproject.toml", "rb") as f:
        pyproject = tomli.load(f)
    return {"version": pyproject["project"]["version"]}


@router.get("/api/config")
async def get_api_config(
    request: Request,
    config: any = Depends(get_config),
) -> JSONResponse:
    return JSONResponse(content=config.get_dict())


# Backoffice static files
@router.get("/backoffice/{file_path:path}")
async def get_backoffice_assets(
    file_path: str, first_frame: bool = False, assets_folder: str = "assets"
):
    if not file_path:
        file_path = "backoffice.html"
    requested_file = f"{assets_folder}/{file_path}"
    # check if file is a gif and first_frame parameter is true
    try:
        if requested_file.endswith(".gif") and first_frame:
            return Response(get_first_frame(requested_file), media_type="image/png")
        else:
            with open(requested_file):
                return FileResponse(str(requested_file))
    except ValueError:
        raise HTTPException(status_code=404, detail="File not found")


# Front page
@router.get("/")
async def get_front_page():
    return FileResponse("assets/index.html")


@router.get("/local/{file_path:path}")
async def get_front_page_assets(file_path: str):
    requested_file = f"assets/{file_path}"
    return FileResponse(requested_file)


# Game static files
@router.get("/game/{game_id}/{file_path:path}")
async def get_player_assets(
    game_id: str,
    file_path: str,
    first_frame: bool = False,
    assets_folder: str = "assets",
):
    if not file_path:
        file_path = "game.html"
    requested_file = f"{assets_folder}/{file_path}"
    try:
        if requested_file.endswith(".gif") and first_frame:
            return Response(get_first_frame(requested_file), media_type="image/png")
        else:
            with open(requested_file):
                return FileResponse(str(requested_file))
    except ValueError:
        raise HTTPException(status_code=404, detail="File not found")


# Gallery static files
@router.get("/gallery/{file_path:path}")
async def get_gallery_assets(
    file_path: str, first_frame: bool = False, assets_folder: str = "assets"
):
    if not file_path:
        file_path = "gallery.html"
    requested_file = f"{assets_folder}/{file_path}"
    # check if file is a gif and first_frame parameter is true
    try:
        if requested_file.endswith(".gif") and first_frame:
            return Response(get_first_frame(requested_file), media_type="image/png")
        else:
            with open(requested_file):
                return FileResponse(str(requested_file))
    except ValueError:
        raise HTTPException(status_code=404, detail="File not found")


class GalleryImageResponse(BaseModel):
    name: str
    path: str


@router.get("/api/gallery", response_model=List[GalleryImageResponse])
async def get_gallery_images() -> List[GalleryImageResponse]:
    images_dir = "assets/images"
    images = []
    for filename in os.listdir(images_dir):
        if filename.endswith(".gif"):
            images.append(
                GalleryImageResponse(
                    name=filename.replace(".gif", ""), path=f"images/{filename}"
                )
            )
    return images


@router.post("/api/gallery", response_model=GalleryImageResponse)
async def upload_image(file: UploadFile = File(...)) -> GalleryImageResponse:
    if not file.filename.endswith(".gif"):
        raise HTTPException(status_code=400, detail="Only GIF files are allowed")
    file_location = f"assets/images/{file.filename}"
    try:
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
        return GalleryImageResponse(
            name=file.filename.replace(".gif", ""), path=f"images/{file.filename}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Create game
@router.post("/api/game")
async def create_game(
    request: GameCreateRequest,
    server: Server = Depends(get_server),
    config: str = Depends(get_config),
) -> GameResponse:
    logger.debug(f"Creating game with request: {request}")
    game = server.create_game(game_id=request.game_id)
    logger.debug(f"Game created: {game}")
    logger.debug(f"Config: {config.MQTT_BROKER}")
    mqtt_client = AsyncMqttClient(
        config.MQTT_BROKER, config.MQTT_PORT, game, config.RESULT_TOPIC
    )
    await mqtt_client.connect()
    game.set_mqtt_client(mqtt_client)
    return GameResponse(**game.model_dump())


# Game status
@router.get("/api/game/{game_id}")
async def get_game(game_id: str, server: Server = Depends(get_server)) -> GameResponse:
    game = server.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return GameResponse(**game.model_dump())


# Start game
@router.post("/api/game/{game_id}")
async def start_game(
    game_id: str, server: Server = Depends(get_server)
) -> GameResponse:
    if server.start_game(game_id):
        game = server.get_game(game_id)
        game.set_task(asyncio.create_task(run_game(game_id, get_server)))
        return game
    raise HTTPException(status_code=404, detail="Game not found")


class CloseAllGamesResponse(BaseModel):
    games_removed: int


@router.delete("/api/game")
async def close_all_games(
    server: Server = Depends(get_server),
) -> CloseAllGamesResponse:
    return CleanupGamesResponse(games_removed=server.close_all_games())


class GameDeleteResponse(BaseModel):
    message: str


@router.delete("/api/game/{game_id}")
async def delete_game(
    game_id: str, server: Server = Depends(get_server)
) -> GameDeleteResponse:
    if server.remove_game(game_id):
        return GameDeleteResponse(message="Game deleted")
    raise HTTPException(status_code=404, detail="Game not found")


class CleanupGamesResponse(BaseModel):
    games_removed: int


@router.patch("/api/game")
async def cleanup_games(server: Server = Depends(get_server)) -> CleanupGamesResponse:
    return CleanupGamesResponse(games_removed=server.cleanup_games())


class GamesListResponse(BaseModel):
    games: List[GameResponse]


@router.get("/api/game", response_model=GamesListResponse)
async def get_games_as_list(server: Server = Depends(get_server)) -> GamesListResponse:
    games = server.get_games()
    games_list = [GameResponse(**game.model_dump()) for game in games]
    return GamesListResponse(games=games_list)


# Add player to game
@router.post("/api/players")
async def add_player_to_game(
    request: PlayerCreateRequest, server: Server = Depends(get_server)
) -> GameResponse:
    logger.debug(f"Adding player to game: {request}")
    game = server.get_game(request.game_id)
    logger.debug(f"Game: {game}...")
    if not game:
        logger.debug(f"Game not found: {request.game_id}")
        raise HTTPException(status_code=404, detail="Game not found")
    elif len(game.players) >= 6:
        logger.debug(f"Game is full: {request.game_id}")
        raise HTTPException(status_code=405, detail="Game is full")
    elif game.status != "waiting":
        logger.debug(f"Game already started: {request.game_id}")
        raise HTTPException(status_code=400, detail="Game already started")

    game.add_player(request.name, request.image_path)
    logger.debug(f"Player added to game: {request}")
    return GameResponse(**game.model_dump())
