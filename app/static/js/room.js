function addRoomToList(roomId, roomName, ownerId) {
  const container = document.getElementById("rooms");

  if (container.querySelector(`[data-room-id="${roomId}"]`)) {
    return;
  }

  const div = document.createElement("div");
  div.className = "room-card";
  div.dataset.roomId = roomId;

  // ownerId is currently always undefined here: the room_created WS event
  // doesn't include it (see api.js's loadRooms(), which does get it from
  // /room/all, for the path where it's actually available). Only append it
  // as a real argument when present, so joinRoom's own `ownerId = null`
  // default applies - quoting `${ownerId}` unconditionally would instead
  // pass the literal string "undefined", which is not null-ish and would
  // wrongly get stored as the room's owner id.
  const ownerArg = ownerId ? `, '${ownerId}'` : "";

  div.innerHTML = `
    <p class="room-card__name">${roomName}</p>
    <button class="btn btn-primary btn-pill" onclick="joinRoom('${roomId}', '${roomName}'${ownerArg})">Join</button>
  `;

  container.appendChild(div);
}