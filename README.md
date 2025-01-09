# Brawlifics = Brawl Stars + Scientifics

## Introduction

Brawlifics is a math-based racing game that combines Brawl Stars characters with educational challenges. Players compete by solving math problems to advance their character along a race track.

## How It Works

1. Manager access backoffice and create a game room and share the room name, or the room link.
1. Players join a game room.
   - Enters their name
   - Selects or uploads a character sprite (stored in `assets/images/`)
   - Waits for other players to join
1. During the game:
   - Players receive math challenges
   - Solving challenges correctly moves their character forward
   - Progress is shown on a race track visualization
   - First player to reach the finish line wins
   - Winner gets a celebration
   - Manager can see the progress in the backoffice

[![Video: HowTo](https://img.youtube.com/vi/jG4_qs6_E4E/0.jpg)](https://www.youtube.com/watch?v=jG4_qs6_E4E)
(Click on the image to watch the video)

## Architecture

### Parts

- `Frontend` for players where they can join the game.
- `Backoffice` for managers to create and monitor games.
- `Backend` server to manage game state and communication.

### Backend

- Built with `FastAPI`, `Python` and using `uv` for project management
- MQTT broker (Mosquitto) handles real-time communication
- Synchronous communication uses HTTP
- Game state management through [`Server`](brawlifics/lib/server.py) class
- No database, all state is in-memory
- Configuration via environment variables (see `.env.example`)
- `Justfile`  is a handy way to save and run project-specific commands. More info [here](https://just.systems/)

### Frontend

- Pure JavaScript with HTML/CSS
- Real-time updates via MQTT over WebSocket
- Key components:
  - [game.js](assets/js/game.js): Main game logic and UI
  - [backoffice.js](assets/js/backoffice.js): Admin interface
- Player states are stored in the browser's `localStorage`

### MQTT Topics

- `brawlifics/game/{game_id}/player/{player}`: Player information
- `brawlifics/game/{game_id}/player/{player}/challenge`: Math challenges
- `brawlifics/game/{game_id}/player/{player}/result`: Players sent challenge results
- `brawlifics/game/{game_id}/status`: Game state updates
- `brawlifics/game/{game_id}/winner`: Winner announcements

## Backoffice

The backoffice interface (`/backoffice`) allows administrators to:

- Create new game rooms
- Monitor active games
- Start/remove games
- Clean up finished games

## Security

- This is not a production-ready application
- No authentication or authorization
- No data validation
- No hidden secrets

## Development Setup

1. MQTT broker is required, if you don't have one, you can use the provided `compose.yml` file to start one:

   ```bash
   docker-compose up mqtt -d
   ```

1. Then start the server:

   ```bash
   uv run uvicorn brawlifics.server:app --reload --log-level debug --host 0.0.0.0 --port 8000
   ```

### Trick for doing it at once

```bash
just run_server_dev
```

## Testing

There are unit tests for player, game, and server classes. Run them with:

```bash
just test_player
just test_game
just test_server
```

## Deployment

Based on Docker, there is a GitHub Action that builds and pushes the image to the GitHub Container Registry.

In the folder `deploy`, there are files to deploy the application using Docker Compose.

If you already have an MQTT broker, just configure .env with the proper credentials and remove the `mqtt` service from the `compose.yml` file.

Typical steps:

1. Adjust the `.env` file inspired by the `.env.example` file.
  - `https` and `wss` are optional, but recommended for production. Set them to `True` in the `.env` file.
  - `https` is not supported for a while, use a reverse proxy.
  - `wss` is supported, but you need to configure the MQTT broker to accept secure connections. Or use your own MQTT broker with `wss` enabled.
1. Check the `compose.yml` file and adjust it if necessary.
1. `compose.yml` maps folder `images` because players can upload images and they have to persist between container restarts.
1. Run the following command:

   ```bash
   docker-compose up -d
   ```

Then application is ready in your URL for players, and in `/backoffice` for managers.

## References

- [Brawl Stars font details](https://fontmeme.com/brawl-stars-font/)
- [Nougat Font](https://fontmeme.com/fonts/nougat-font/)
