function get_config() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/config', false); // false for synchronous
  xhr.send(null);
  if (xhr.status === 200) {
    const data = xhr.responseText;
    const config = JSON.parse(data);
    console.debug('config:', config);
    return config;
  } else {
    console.error('Error fetching config:', xhr.statusText);
    throw new Error(`HTTP error! status: ${xhr.status}`);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.config = get_config();

  document.ldcv = new ldcover({ root: ".ldcv" });
  const table = document.getElementById('games-table');
  const form = document.getElementById('add-room-form');
  const cleanupButton = document.getElementById('cleanup-button');
  const closeAllButton = document.getElementById('close-all-button');
  // Fetch and display all rooms
  fetchRooms();

  // Add input validation for room name
  const nameInput = form.querySelector('.name');
  nameInput.addEventListener('keypress', (e) => {
    // Only allow alphanumeric characters
    if (!(/[a-zA-Z0-9]/).test(e.key)) {
      e.preventDefault();
    }
  });

  // Also prevent paste of invalid characters
  nameInput.addEventListener('paste', (e) => {
    e.preventDefault();
    const text = (e.clipboardData || window.clipboardData).getData('text');
    const validText = text.replace(/[^a-zA-Z0-9]/g, '');
    document.execCommand('insertText', false, validText);
  });


  // Add new room
  form.addEventListener('submit', handleFormSubmit);
  cleanupButton.addEventListener('click', handleCleanup);
  closeAllButton.addEventListener('click', handleCloseAll);

  // mqtt connection
  document.client = mqtt.connect(
    document.config.MQTT_URL, {
    clean: true,
    clientId: Math.random().toString(36).substring(7),
    protocolVersion: 4,
    username: document.config.MQTT_BO_USER,
    password: document.config.MQTT_BO_PASS
  });
  // set callback handlers
  document.client.on('connect', onConnect);
  document.client.on('disconnect', onConnectionLost);
  document.client.on('message', (topic, message) => onMessageArrived(topic, message));

  // called when the client connects
  function onConnect() {
    console.debug("MQTT connected");
    document.client.subscribe("brawlifics/game/+/status");
    console.debug("Subscribed to brawlifics/game/+/status");
    document.client.subscribe("brawlifics/game/+/players");
    console.debug("Subscribed to brawlifics/game/+/players");
    // client.subscribe("brawlifics/game/+/winner");
  }

  // called when the client loses its connection
  function onConnectionLost(responseObject) {
    if (responseObject.errorCode !== 0) {
      console.error("onConnectionLost:" + responseObject.errorMessage);
    }
  }

  /**
   * @param {string} topic
   * @param {Buffer} message
   */
  function onMessageArrived(topic, message) {
    console.debug(`onMessageArrived: ${topic} - ${message.toString()}`);
    if (topic.match(/^brawlifics\/game\/[^/]+\/players$/)) {
      console.debug('Received players message');
      const gameId = topic.split('/')[2];
      // check if the game is in the table
      const row = document.getElementById(`data-game-id-${gameId}`);
      const parsed_message = JSON.parse(message.toString());
      if (row) {
        const players = Object.values(parsed_message.players);
        row.cells[2].innerHTML = players.map(player => `${player.name} (${player.position})<br />`).join('');
      } else {
        console.debug('adding new game to table');
        addRoomToTable(parsed_message);
      }
    } else if (topic.match(/^brawlifics\/game\/[^/]+\/status$/)) {
      const gameId = topic.split('/')[2];
      const statusCell = document.getElementById(`status-${gameId}`);
      statusCell.innerHTML = message.toString();
    }
  }
});

function handleCleanup() {
  document.ldcv.get()
    .then(function (ret) {
      if (ret == 1) {
        fetch('/api/game', {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json'
          }
        })
          .then(response => response.json())
          .then(data => {
            console.debug('Rooms cleaned up:', data);
            if (data.games_removed === 0) {
              return;
            }
            const table = document.getElementById('games-table');
            // remove all rows from the table, not headers
            while (table.rows.length > 1) {
              table.deleteRow(1);
            }
            fetchRooms();
          })
          .catch(error => {
            console.error('Error cleaning up rooms:', error);
          });
      }
    });
}

function handleCloseAll() {
  document.ldcv.get()
    .then(function (ret) {
      if (ret == 1) {
        fetch('/api/game', {
          method: 'DELETE',
        })
          .then(response => response.json())
          .then(data => {
            console.debug('All games closed:', data);
            if (data.games_closed === 0) {
              return;
            }
            const table = document.getElementById('games-table');
            // remove all rows from the table, not headers
            while (table.rows.length > 1) {
              table.deleteRow(1);
            }
            fetchRooms();
          });
      }
    });
}

/**
 * Fetch all rooms from the API and display them in the table.
 */
function fetchRooms() {
  fetch('/api/game', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then(response => response.json())
    .then(data => {
      console.debug('games:', data);
      data.games.forEach(game => {
        console.debug('game:', game);
        addRoomToTable(game);
      });
    })
    .catch(error => {
      console.error('Error fetching rooms:', error);
    });
}

/**
 * Handle the form submission to add a new room.
 * @param {Event} event - The submit event.
 */
function handleFormSubmit(event) {
  event.preventDefault();

  const roomName = event.target.querySelector('.name').value;
  const message = {
    game_id: roomName
  };

  fetch('/api/game', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(message)
  })
    .then(response => response.json())
    .then(data => {
      addRoomToTable(data);
    })
    .catch(error => {
      console.error('Error creating room:', error);
    });
}

/**
 * Add a game_id to the table.
 * @param {Object} game - The game_id to add.
 */
function addRoomToTable(game) {
  console.debug('addRoomToTable:', game);
  const table = document.getElementById('games-table').querySelector('tbody');
  const newRow = table.insertRow();
  newRow.id = `data-game-id-${game.game_id}`;

  const nameCell = newRow.insertCell(0);
  const statusCell = newRow.insertCell(1);
  const playersCell = newRow.insertCell(2);
  const linkCell = newRow.insertCell(3);
  const actionsCell = newRow.insertCell(4);

  nameCell.innerHTML = game.game_id;
  statusCell.innerHTML = game.status;
  statusCell.id = `status-${game.game_id}`;

  // iterate game.players and add them to the cell
  console.debug('game.players:', Object.keys(game.players).length);
  // check if game.players is an object
  if (typeof game.players === 'object' && Object.keys(game.players).length > 0) {
    const sortedPlayers = Object.values(game.players)
      .sort((a, b) => b.position - a.position);

    sortedPlayers.forEach((player, index) => {
      const position = index + 1;
      playersCell.innerHTML += `${position}. ${player.name} (${player.position})<br />`;
    });
  } else {
    playersCell.innerHTML = "None";
  }

  const link = `/game/${game.game_id}`;
  const fullLink = window.location.origin + link;

  linkCell.innerHTML = `<a href="${link}">${fullLink}</a>`;

  // Create delete button
  const deleteButton = document.createElement('button');
  deleteButton.className = 'button delete-button';
  deleteButton.innerHTML = '<i class="fa-solid fa-trash"></i>';
  deleteButton.addEventListener('click', () => {
    document.ldcv.get()
      .then(function (ret) {
        if (ret == 1) {
          handleDeleteRoom(game.game_id, newRow);
        }
      });
  });
  deleteButton.style.display = 'inline-block';

  // Create start button
  const startButton = document.createElement('button');
  startButton.id = 'start-button-' + game.game_id;
  startButton.className = 'button start-button';
  startButton.innerHTML = '<i class="fa-solid fa-play"></i>';
  startButton.addEventListener('click', () => {
    startButton.style.display = 'none';
    handleStartGame(game.game_id, newRow);
  });
  if (game.status === 'playing' || game.status === 'finished') {
    startButton.style.display = 'none';
  } else {
    startButton.style.display = 'inline-block';
  }

  // Append buttons to the actions cell
  actionsCell.appendChild(deleteButton);
  actionsCell.appendChild(startButton);
}

function handleStartGame(game_id, row) {
  fetch("/api/game/" + game_id, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ game_id: game_id })
  })
    .then(response => response.json())
    .then(data => {
      console.debug('Game started:', data);
      if (data.status !== 'playing') {
        console.error('Error starting game:', data);
        return;
      }
      row.cells[1].innerHTML = data.status;
    })
    .catch(error => {
      console.error('Error starting game:', error);
    });
}

/**
 * Handle the deletion of a room.
 * @param {string} game_id - The game ID of the room to delete.
 * @param {HTMLTableRowElement} row - The table row to remove.
 */
function handleDeleteRoom(game_id, row) {
  fetch("/api/game/" + game_id, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ game_id: game_id })
  })
    .then(response => response.json())
    .then(data => {
      console.debug('Room deleted:', data);
      row.remove();
    })
    .catch(error => {
      console.error('Error deleting room:', error);
    });
}
