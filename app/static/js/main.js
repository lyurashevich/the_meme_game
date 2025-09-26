document.getElementById("sendMessage").addEventListener("click", () => {
  const messageInput = document.getElementById("chatMessage");
  const message = messageInput.value.trim();

  if (!message) return;

  if (!currentRoomId) {
    alert("You have to be joined to the room");
    return;
  }

  if (!ws || ws.readyState !== WebSocket.OPEN) {
    alert("WebSocket connection has not established");
    return;
  }

  ws.send(JSON.stringify({
    event: 'chat_message',
    room_id: currentRoomId,
    message: message
  }));

  messageInput.value = '';
})

document.getElementById('chatMessage').addEventListener('keypress', (e) => {
  if (e.key == 'Enter') {
    document.getElementById('sendMessage').click();
  }
});

document.getElementById("createRoomBtn").addEventListener("click", async () => {
  if (!playerId) {
    log("Сначала подключитесь!");
    return;
  }

  try {
    const response = await fetch("/room/", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ player_id: playerId })
  });

  const room = await response.json();
  log("Создана комната: " + JSON.stringify(room, null, 2));

  showRoomInterface(room.id, room.name);
  await loadChatHistory(room.id);
} catch (error) {
  log("ошибка создания комнаты: " + error);
}
});

document.getElementById("leaveRoomBtn").addEventListener("click", async () => {
  if (!playerId || !currentRoomId) {
    log("you are not in the room");
    return;
  }

  try {
    const response = await fetch(`/room/${currentRoomId}/leave`, {
      method: "PATCH",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ player_id: playerId })
    });

    if (!response.ok) {
      const error = await response.json();
      log("an error occured during leavin the room: " + error.detail);
      return;
    }

    log("you have left the room: " + currentRoomId);

    hiddenRoomInterface();
    await loadRooms();
  } catch (error) {
    log("an error occured during leaving the room: " + error)
  }
});

document.getElementById("startGameBtn").addEventListener("click", async () => {
  if (!playerId || !currentRoomId) {
    log("you have to be joined to the room to start game");
    return;
  }

  try {
    const response = await fetch(`/game/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ room_id: currentRoomId })
    });

    if (!response.ok) {
      const error = await response.json();
      log("Failed to start game: " + error.detail);
      return;
    }

    const result = await response.json();
    log("The game started: " + JSON.stringify(result));

    const roundResponse = await fetch(`/round/${currentRoomId}/start`, {
      method: "POST"
    });

    if (!roundResponse.ok) {
      const error = await roundResponse.json();
      log("Failed to start first round: " + error.detail);
      return;
    }

    const roundData = await roundResponse.json();
    log("First round started: " + JSON.stringify(roundData));

    renderRound(roundData);

  } catch (error) {
    log("failed to start game: " + error);
  }
})