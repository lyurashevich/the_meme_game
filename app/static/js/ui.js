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

// Clears all in-game UI + client state. Used both when the current player
// leaves a room and when the game is ended for the players who stay.
function resetGameUI() {
  const cardsContainer = document.getElementById('cardsContainer');
  if (cardsContainer) cardsContainer.innerHTML = '';

  if (typeof clearTable === 'function') {
    clearTable();
  } else {
    const table = document.getElementById('tableArea');
    if (table) table.innerHTML = '';
  }

  const roundInfo = document.getElementById('roundInfo');
  if (roundInfo) roundInfo.innerHTML = '';

  ['playerCards', 'tableArea', 'confirmChoice', 'confirmWinner', 'score'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
  });

  // Reset shared game globals (declared across main.js / game.js / ws.js).
  isLeader = false;
  selectedCardId = null;
  selectedWinnerCardId = null;
  cardsReceived = 0;
  leaderChoosingPhaseInitialized = false;
  pendingPhase = null;

  if (typeof phaseTimeout !== 'undefined' && phaseTimeout) {
    clearTimeout(phaseTimeout);
    phaseTimeout = null;
  }
}

function hiddenRoomInterface() {
  currentRoomId = null;
  currentRoomName = null;

  resetGameUI();

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