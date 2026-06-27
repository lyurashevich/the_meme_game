async function joinRoom(roomId, roomName) {
  try {
    const response = await fetch(`/room/${roomId}`, {
      method: "PATCH",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        player_id: playerId
      })
    });

    if (response.ok) {
      currentRoomId = roomId;
      document.getElementById('chatContainer').classList.remove('hidden');
      await showRoomInterface(roomId, roomName);
      await loadChatHistory(roomId);
    } else {
      const error = await response.json();
      alert("error: " + error.detail);
    }
  } catch (error) {
    alert ("connection error: " + error);
  }
}

async function loadRooms() {
  try {
    const response = await fetch("/room/all");
    const rooms = await response.json();

    const container = document.getElementById("rooms");
    container.innerHTML = "";

    rooms.forEach(room => {
      const div = document.createElement("div");
      div.innerHTML = `
        <p>Room: ${room.name} | Players: ${room.players_count}/${room.max_players}</p>
        <button onclick="joinRoom('${room.id}', '${room.name}')">Join room</button>
      `;
      container.appendChild(div);
    });
  } catch (error) {
    log("error: " + error);
  }
}

function updateUsername(newName) {
  return fetch(`/player/${playerId}/profile`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: newName })
  })
    .then(res => res.json())
    .then(data => {
      document.querySelector("#username").textContent = data.username;
    });
  }

document.querySelector("#saveSettingsBtn").addEventListener("click", () => {
    const newName = document.querySelector("#settingsUsername").value;
    updateUsername(newName);
});

function loadProfile(playerId) {
  fetch(`/player/${playerId}/profile`)
    .then(res => res.json())
    .then(data => {
      document.querySelector("#avatar").src =
        `/avatars/avatar_${data.avatar}.png`;

      document.querySelector("#username").textContent = data.username;
    });
  }

let avatar = document.querySelector("#avatar");
const modal = document.querySelector("#settingsModal");

avatar.addEventListener("click", () => {
  modal.classList.remove("hidden");

  document.querySelector("#settingsUsername").value =
    document.querySelector("#username").textContent;
});

document.querySelector("#closeSettingsBtn").addEventListener("click", () => {
  modal.classList.add("hidden");
});
