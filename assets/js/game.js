// @ts-check
function onConnect() {
  localStorage.setItem("mqtt_connected", "true");

  const game_id = localStorage.getItem("game_id");
  document.client.subscribe(`brawlifics/game/${game_id}/status`);
  document.client.subscribe(`brawlifics/game/${game_id}/players`);
  document.client.subscribe(`brawlifics/game/${game_id}/winner`);
}

function onConnectionLost(responseObject) {
  localStorage.setItem("mqtt_connected", "false");
  if (responseObject.errorCode !== 0) {
    console.debug("onConnectionLost:" + responseObject.errorMessage);
  }
}

/**
 * @param {string} topic
 * @param {Buffer} message
 */
async function onMessageArrived(topic, message) {
  console.debug(`onMessageArrived: ${topic} - ${message.toString()}`);
  const game_id = localStorage.getItem("game_id");
  const player_name = localStorage.getItem("player_name");
  if (topic === `brawlifics/game/${game_id}/players`) {
    console.debug('Received players message');
    localStorage.setItem("game", message.toString());
    update_players();
  } else if (topic === `brawlifics/game/${game_id}/player/${player_name}/challenge`) {
    console.debug('Received challenge message');
    localStorage.setItem("challenge", message.toString());
    challenged(message.toString());
  } else if (topic === `brawlifics/game/${game_id}/winner`) {
    console.debug('Received winner message');
    localStorage.setItem("winner", message.toString());
    const _winner = localStorage.getItem("winner");
    if (_winner == player_name) {
      winner();
    } else {
      finished();
    }
  } else if (topic === `brawlifics/game/${game_id}/status`) {
    localStorage.setItem("status", message.toString());
  }
}

function winner() {
  console.debug("winner");
  document.game_status.querySelector(".game-waiting").style.display = "none";
  document.game_status.querySelector(".game-finished").style.display = "none";
  document.querySelector("#game-status-container").style.display = "none";
  document.getElementById("canvas-text").style.display = "block";
  document.getElementById("canvas").style.display = "block";
  confetti();
}

function finished() {
  console.debug("finished");
  document.game_status.style.display = "block";
  document.game_status.querySelector(".game-waiting").style.display = "none";
  document.querySelector("#game-status-container").style.display = "none";
  const finished = document.game_status.querySelector(".game-finished");
  finished.style.display = "block";
  const game = JSON.parse(localStorage.getItem("game"));
  // sort players by position in descending order
  const sortedPlayers = Object.values(game.players).sort((a, b) => b.position - a.position);
  const player_name = localStorage.getItem("player_name");
  finished.querySelector("#your_position").innerHTML = sortedPlayers.findIndex(player => player.name === player_name) + 1;
}

/**
 * @param {string} challenge
 */
async function challenged(challenge) {
  console.debug("challenged");
  const game_id = localStorage.getItem("game_id");
  const player_name = localStorage.getItem("player_name");
  document.querySelector("#game-status").style.display = "none";
  document.querySelector("#game-status-container").style.display = "grid";
  const answer = document.getElementById("answer")
  answer.focus();
  // answer.addEventListener('keypress', (e) => {
  //   if (e.key === 'Enter') {
  //     document.querySelector("#challenge_submit_button").click();
  //   }
  // });
  const parsed_challenge = challenge.replace(/\*/g, 'x');
  document.querySelector("#challenge").innerHTML = parsed_challenge;
  document.querySelector("#challenge_submit_button").onclick = () => {
    const answer = document.getElementById("answer");
    submit_answer(challenge, game_id, player_name, answer.value);
    answer.value = "";
  }
}

/**
 * @param {string} challenge
 * @param {string | null} game_id
 * @param {string | null} player_name
 * @param {string} answer
 */
function submit_answer(challenge, game_id, player_name, answer) {
  // challenge is a string with a mathematical operation, check if answer is correct
  const result = eval(challenge);
  console.debug(`challenge: ${challenge} = result: ${result} - answer: ${answer}`);

  if (parseInt(answer) === parseInt(result)) {
    console.debug(`submitting answer: ${answer}`);
    const topic = `brawlifics/game/${game_id}/player/${player_name}/result`;
    document.client.publish(topic, answer);
    document.querySelector(".challenge-form h2").innerHTML = "<span class='verd'><i class='fa-solid fa-check'></i> Correcte!</span><br>Nou repte:";
  } else {
    document.querySelector(".challenge-form h2").innerHTML = "<span class='vermell'><i class='fa-solid fa-xmark'></i> Incorrecte!</span><br>Torna-ho a provar:";
    console.debug(`answer: ${answer} is incorrect`);
  }
}

async function register_player() {
  console.debug("register_player");
  updateStatus("Registrant jugador... <i class='fa-solid fa-hourglass-half'></i>");
  // await new Promise(resolve => setTimeout(resolve, 2000));
  await fetch("/api/players", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      name: localStorage.getItem("player_name"),
      game_id: localStorage.getItem("game_id"),
      image_path: localStorage.getItem("player_image")
    })
  })
    .then(response => {
      console.debug(response.status, response.statusText);
      if (response.status == 200) {
        return response.json();
      } else if (response.status == 400) {
        updateStatus("<i class='fa-solid fa-ban'></i><br>Partida iniciada!<br>Ja no es poden afegir jugadors.");
        document.getElementById("player-panel").style.display = "none";
        throw new Error("Game already started");
      } else if (response.status == 405) {
        updateStatus("<i class='fa-solid fa-ban'></i><br>Sala plena!");
        document.getElementById("player-panel").style.display = "none";
        throw new Error("Game is full");
      } else if (response.status == 404) {
        updateStatus("<i class='fa-solid fa-ban'></i><br>Aquesta sala no existeix!");
        document.getElementById("player-panel").style.display = "none";
        throw new Error("Aquesta sala no existeix!");
      } else {
        throw new Error("Error registering player");
      }
    })
    .then(data => {
      console.debug("Player registered:", data);
      updateStatus("Jugador registrat! <i class='fa-solid fa-check'></i>");
      localStorage.setItem("game", JSON.stringify(data));
      update_players();
    });
}

/**
 * @param {string} message
 */
function updateStatus(message) {
  document.getElementById("player-panel").style.display = "none";
  // document.game_status.querySelector(".game-waiting").style.display = "block";
  const msg = document.game_status.querySelector(".game-waiting h2")
  msg.innerHTML = message;
  msg.innerHTML += `<br><button onclick="window.location.href='/'" class="submit-button" style="font-size: 1em;">Tornar a l'inici</button>`;
}

function update_players() {
  console.debug("update_players");
  document.getElementById("player-panel").style.display = "block";
  const game = JSON.parse(localStorage.getItem("game"));
  const player_name = localStorage.getItem("player_name");

  const table = document.getElementById("players-table");
  const table_body = table.querySelector("tbody");
  console.debug("table_body", table_body);

  // Sort players by position in descending order
  const sortedPlayers = Object.values(game.players).sort((a, b) => b.position - a.position);

  // Clear existing table rows
  while (table_body.firstChild) {
    table_body.removeChild(table_body.firstChild);
  }

  // Add sorted players to table
  sortedPlayers.forEach(player => {
    const row = table_body.insertRow();
    row.id = `player-${player.name}`;
    row.insertCell(0).innerHTML = player.name;
    row.insertCell(1).innerHTML = player.position;
  });


  update_race_tracks();
}

function update_race_tracks() {
  console.debug("update_race_tracks");
  const game = JSON.parse(localStorage.getItem("game"));
  // Clear existing race tracks
  const raceTracks = document.getElementById("race-tracks");
  console.debug("initial: raceTracks", raceTracks);
  if (localStorage.getItem("status") !== "playing") {
    raceTracks.innerHTML = "";
    console.debug("cleared: raceTracks", raceTracks);
    // Add race track for each player
    Object.values(game.players).forEach((player, index) => {
      raceTracks.appendChild(add_race_track(player.name, player.image_path));
    });
    console.debug("updated: raceTracks", raceTracks);
  } else {
    Object.values(game.players).forEach((player, index) => {
      moveRunner(player.name, Math.floor(player.position), player.image_path);
    });
    console.debug("updated characters");
  }

}

/**
 * @param {string | null} player_name
 * @param {any} image_path
 */
function add_race_track(player_name, image_path) {
  const track = document.createElement("div");
  track.className = "race-track";
  track.id = `player-track-${player_name}`;

  const finish_flag = document.createElement("i");
  finish_flag.className = "fas fa-flag-checkered finish-flag";
  finish_flag.id = `player-finish-flag-${player_name}`;

  const name = document.createElement("h3");
  name.id = `player-track-name-${player_name}`;
  name.textContent = player_name;
  if (player_name == localStorage.getItem("player_name")) {
    name.classList.add("you");
  }

  const runner = document.createElement("img");
  runner.src = `${image_path}?first_frame=true`; // Start with static image
  runner.className = "runner pos-0";
  runner.id = `player-runner-image-${player_name}`;
  runner.setAttribute('data-position', '0'); // Initialize position data

  track.appendChild(name);
  track.appendChild(runner);
  track.appendChild(finish_flag);
  return track;
}

async function get_name() {
  const player_name = localStorage.getItem("player_name");
  const game_id = localStorage.getItem("game_id");

  if (player_name) {
    console.debug(`subscribing to challenge for ${player_name} and game ${game_id}`);
    document.getElementById("player-name").innerHTML = player_name;
    document.client.subscribe(`brawlifics/game/${game_id}/player/${player_name}/challenge`);

    return await register_player();
  }
  await document.form_nom.get()
    .then(async function (/** @type {string} */ ret) {
      if (ret === "1") {
        const player_name = document.getElementById("name").value;
        localStorage.setItem("player_name", player_name);
        document.getElementById("player-name").innerHTML = player_name;
        document.client.subscribe(`brawlifics/game/${game_id}/player/${player_name}/challenge`);

        return await register_player();
      } else {
        return location.reload();
      }
    });
}

function confetti() {
  let W = window.innerWidth;
  let H = window.innerHeight;
  const canvas = document.getElementById("canvas");
  const context = canvas.getContext("2d");
  const maxConfettis = 150;
  const particles = [];

  const possibleColors = [
    "DodgerBlue",
    "OliveDrab",
    "Gold",
    "Pink",
    "SlateBlue",
    "LightBlue",
    "Gold",
    "Violet",
    "PaleGreen",
    "SteelBlue",
    "SandyBrown",
    "Chocolate",
    "Crimson"
  ];

  /**
   * @param {number} from
   * @param {number} to
   */
  function randomFromTo(from, to) {
    return Math.floor(Math.random() * (to - from + 1) + from);
  }

  function confettiParticle() {
    this.x = Math.random() * W; // x
    this.y = Math.random() * H - H; // y
    this.r = randomFromTo(11, 33); // radius
    this.d = Math.random() * maxConfettis + 11;
    this.color =
      possibleColors[Math.floor(Math.random() * possibleColors.length)];
    this.tilt = Math.floor(Math.random() * 33) - 11;
    this.tiltAngleIncremental = Math.random() * 0.07 + 0.05;
    this.tiltAngle = 0;

    this.draw = function () {
      context.beginPath();
      context.lineWidth = this.r / 2;
      context.strokeStyle = this.color;
      context.moveTo(this.x + this.tilt + this.r / 3, this.y);
      context.lineTo(this.x + this.tilt, this.y + this.tilt + this.r / 5);
      return context.stroke();
    };
  }

  function Draw() {
    const results = [];

    // Magical recursive functional love
    requestAnimationFrame(Draw);

    context.clearRect(0, 0, W, window.innerHeight);

    for (var i = 0; i < maxConfettis; i++) {
      results.push(particles[i].draw());
    }

    let particle = {};
    let remainingFlakes = 0;
    for (var i = 0; i < maxConfettis; i++) {
      particle = particles[i];

      particle.tiltAngle += particle.tiltAngleIncremental;
      particle.y += (Math.cos(particle.d) + 3 + particle.r / 2) / 2;
      particle.tilt = Math.sin(particle.tiltAngle - i / 3) * 15;

      if (particle.y <= H) remainingFlakes++;

      // If a confetti has fluttered out of view,
      // bring it back to above the viewport and let if re-fall.
      if (particle.x > W + 30 || particle.x < -30 || particle.y > H) {
        particle.x = Math.random() * W;
        particle.y = -30;
        particle.tilt = Math.floor(Math.random() * 10) - 20;
      }
    }

    return results;
  }

  window.addEventListener(
    "resize",
    function () {
      W = window.innerWidth;
      H = window.innerHeight;
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    },
    false
  );

  // Push new confetti objects to `particles[]`
  for (var i = 0; i < maxConfettis; i++) {
    particles.push(new confettiParticle());
  }

  // Initialize
  canvas.width = W;
  canvas.height = H;
  Draw();
}

/**
 * @param {string | null} player_name
 * @param {string | number} position
 * @param {any} image_path
 */
function moveRunner(player_name, position, image_path) {
  const runner = document.getElementById(`player-runner-image-${player_name}`);
  const currentPosition = runner.getAttribute('data-position') || '0';
  const numericCurrentPosition = parseInt(currentPosition);
  const numericNewPosition = parseInt(position);

  // Disable answer input during animation
  if (numericCurrentPosition !== numericNewPosition && answer && player_name == localStorage.getItem("player_name")) {
    const answer = document.getElementById("answer");
    const challenge_submit_button = document.getElementById("challenge_submit_button");

    answer.disabled = true;
    answer.style.opacity = "0.2";
    challenge_submit_button.disabled = true;
    challenge_submit_button.style.opacity = "0.2";
    setTimeout(() => {
      answer.disabled = false;
      answer.style.opacity = "1";
      challenge_submit_button.disabled = false;
      challenge_submit_button.style.opacity = "1";
    }, 3000);
  }



  if (numericCurrentPosition !== numericNewPosition) {
    runner.src = image_path;
    runner.classList.remove(`pos-${currentPosition}`);
    runner.classList.add(`pos-${position}`);
    // After animation completes, switch to static image
    setTimeout(() => {
      runner.src = `${image_path}?first_frame=true`;
    }, 3000);
  }
  // Store the new position as data attribute
  runner.setAttribute('data-position', position);
}

function generateTrackPositions() {
  const style = document.createElement('style');
  const positions = [];

  // Calculate percentage for each position
  const steps = Math.floor(document.config.TRACK_LENGTH); // Multiply by 10 to get more granular positions
  for (let i = 0; i <= steps; i++) {
    const percentage = (i / steps) * 100;
    positions.push(`.runner.pos-${i} { left: ${percentage}%; }`);
    console.debug(`.runner.pos-${i} { left: ${percentage}%; }`);
  }

  style.textContent = positions.join('\n');
  document.head.appendChild(style);
}

async function get_config() {
  const response = await fetch("/api/config");
  if (!response.ok) {
    throw new Error("Error fetching config");
  }

  const config = await response.json();
  console.debug("config: ", config);
  return config;
}


document.addEventListener('DOMContentLoaded', async () => {
  localStorage.removeItem("status");
  localStorage.removeItem("challenge");
  localStorage.removeItem("winner");
  localStorage.removeItem("game");
  localStorage.setItem("mqtt_connected", "false");
  document.config = await get_config();
  if (localStorage.getItem("player_image") == null) {
    // location.href = "/gallery?back=" + window.location.href;
    localStorage.setItem('player_image', 'images/bs_leon_run.gif');
  }
  generateTrackPositions();
  document.form_nom = new ldcover({ root: "#name-modal" });
  document.game_status = document.getElementById("game-status");
  document.querySelector("#game-status-container").style.display = "none";
  document.game_status.querySelector(".game-finished").style.display = "none";
  const game_id = location.pathname.split("/")[2];
  if (game_id) {
    localStorage.setItem("game_id", game_id);
    const el_sala = document.getElementById("sala");
    el_sala.innerHTML = game_id;
  } else {
    console.error("No game_id found");
    return;
  }

  // mqtt connection
  // Number(location.port),
  // hosts: ["ws://brawlifics.riusbarbera.family:9001"]
  document.client = mqtt.connect(
    document.config.MQTT_URL, {
    clean: true,
    clientId: Math.random().toString(36).substring(7),
    protocolVersion: 4,
    username: document.config.MQTT_FE_USER,
    password: document.config.MQTT_FE_PASS
  });
  document.client.on('connect', onConnect);
  document.client.on('disconnect', onConnectionLost);
  document.client.on('message', (topic, message) => onMessageArrived(topic, message));

  updateStatus("Connectant al servidor... <i class='fa-solid fa-spinner'></i>");
  while (localStorage.getItem("mqtt_connected") !== "true") {
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  updateStatus("Connectat a MQTT! <i class='fa-solid fa-check'></i>");

  try {
    await get_name();
    updateStatus("Esperant jugadors... <i class='fa-solid fa-hourglass-half'></i>");
  } catch (error) {
    console.error(error);
    return;
  }
});
