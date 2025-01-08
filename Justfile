test_player_journey:
    uv run pytest tests/test_player_journey.py -v --log-cli-level=INFO

test_player:
    uv run pytest tests/test_player.py -v --log-cli-level=INFO

test_game:
    uv run pytest tests/test_game.py -v --log-cli-level=INFO

test_server:
    uv run pytest tests/test_server.py -v --log-cli-level=INFO

run_server:
    uv run python server.py 

run_server_dev:
    docker compose down mqtt
    docker compose up mqtt -d
    uv run uvicorn brawlifics.server:app --reload --log-level debug --host 0.0.0.0 --port 8000

run:
    uv run uvicorn server:app --log-level info --host 0.0.0.0 --port 8000

install:
    uv install
