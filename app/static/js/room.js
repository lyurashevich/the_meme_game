function addRoomToList(roomId, roomName) {
  const container = document.getElementById("rooms");

  if (container.querySelector(`[data-room-id="${roomId}"]`)) {
    return;
  }

  const div = document.createElement("div");
  div.dataset.roomId = roomId;

  div.innerHTML = `
    <p>Room: ${roomName}</p>
    <button onclick="joinRoom('${roomId}', '${roomName}')">Join</button
  `;

  container.appendChild(div);
}