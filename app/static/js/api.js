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
      log('you have joine the room: ' + roomId);
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