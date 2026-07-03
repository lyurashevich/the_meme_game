let playerId = null;
let currentRoomId = null;
let currentRoomName = null;
let isLeader = false

function updateLeaderStatus(leaderId) {
  isLeader = (playerId === leaderId);
}

function showRoomInterface(roomId, roomName) {
  currentRoomId = roomId;
  currentRoomName = roomName;

  document.getElementById('roomInfo').classList.remove('hidden');
  document.getElementById('currentRoomName').textContent = roomName;

  document.getElementById('chatContainer').classList.remove('hidden');

  document.getElementById('rooms').classList.add('hidden');
  document.getElementById('connectBtn').classList.add('hidden');
  document.getElementById('createRoomBtn').classList.add('hidden');
  document.getElementById('startGameBtn').classList.remove('hidden');
}

function hiddenRoomInterface() {
  currentRoomId = null;
  currentRoomName = null;

  document.getElementById('roomInfo').classList.add('hidden');
  document.getElementById('chatContainer').classList.add('hidden');
  document.getElementById('startGameBtn').classList.add('hidden');

  document.getElementById('rooms').style.display = 'inline-block';
//  document.getElementById('createRoomBtn').style.display = 'inline-block';
  document.getElementById('createRoomBtn').classList.remove("hidden");

  document.getElementById('messages').innerHTML = '';
  document.getElementById('chatMessage').value = '';
}

function log(msg) {
  document.getElementById("log").textContent += msg + "\n";
}