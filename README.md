# Brawlifics = Brawl Stars + Scientifics

## Introduction

Typical camel race where the camels are replaced by Brawlers. The game is played on a track with a length of 10 km. There up to 6 Brawlers playing at the same time on the network.

When a player is connected to the URL, the player has to provide a name and the player can select a Brawler already uploaded, or upload a new one using a PNG file with fixed size.

Central server will be responsible for the game logic and the game will be played in real time. When all player are ready there is a countdown and the game starts.

At the same time each player will receive a simple mathematics operation challenge, for instance, a simple add, subtract or multiply operation. The player has to solve the operation and send the result to the server. The fastest the playe answer the correct result, the faster the Brawler will move.

When there is a winner the game will be over and the winner will be announced.

## Technologies

Backend is created using Python and FastAPI, the communication between the server and the player is done using MQTT over Websockets.

Server will have also a web interface to show the game status and the players progress. And the server will support multitenancy, depending on the URL the player is connected to, the player will be assigned to a different game.

Player interface will be a simple HTML page with JavaScript to handle the MQTT communication. Also using the JavaScript the Brawler will move on the track.

## MQTT topics

- `brawlifics/game/<game_id>/challenge`: Server will send the challenge to the player. The challenge will be a simple math operation evaluable by the Python `eval` function.
- `brawlifics/game/<game_id>/player/<player_id>`: Server will send the player information to the player. The player information will be:
  - `result`: The result of the operation.
  - `position`: The position of the player in the track. The position will be a float number between 0 and 100.
  - `character`: The character the player is using.
  - `name`: The name of the player.
  - `status`: The status of the player. The status can be `playing`, `waiting`, `winner` or `loser`.

## Server management interface

The server will have a web interface to manage the games. The interface will be a simple HTML page with JavaScript to handle the MQTT communication.

Because this is multitenant server, the interface will allow to manage the tenants, so it allow to create a new game, stop a game, and see the game history.

Per each tenant the interface will show the games in progress and the players in each game. The interface will allow to start a new game, stop a game, and see the game history.

## Player interface

The player interface will be a simple HTML page with JavaScript to handle the MQTT communication. The player will see the track with the Brawlers moving and the player will see the challenge to solve.

The player will have to solve the challenge and send the result to the server. The player will see the position of the player in the track and the position of the other players.

## Storage

Persitent data will be sabed in JSON files in the server. The server will have a folder for each tenant and inside the folder there will be a JSON file per each game.

## Set-up

1. Install Poetry:

  ```bash
  curl -sSL https://install.python-poetry.org | python3 -
  ```

1. Clone the repository and install dependencies:

  ```bash
  git clone ssh://git@git.oriolrius.cat:222/oriolrius/brawlifics.git
  cd brawlifics
  poetry install
  ```

1. Create a `.env` file with the environment variables. You can use the `.env.example` as a template.

```bash
cp .env.example .env
```

1. Run the server:

```bash
poetry run uvicorn server:app --reload
```

Or use the Justfile command:

```bash
just run
```

## Development

Format the code:

```bash
poetry run black
```

To run the tests:

```bash
poetry run pytest
```
