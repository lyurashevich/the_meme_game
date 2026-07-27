let playerId = null;
let currentRoomId = null;
let currentRoomName = null;
let currentRoomOwnerId = null; // id владельца текущей комнаты; нужен, чтобы решить, показывать ли кнопку настроек
let isLeader = false

function updateLeaderStatus(leaderId) {
  isLeader = (playerId === leaderId);
}

// ownerId — необязательный (третий) аргумент. Если вызывающий его знает (создание/вход из списка),
// передаёт; если нет (например, переподключение в ws.js) — не передаёт, и мы не затираем то,
// что уже знали. Значение по умолчанию `null` срабатывает, только когда аргумент вообще опущен.
function showRoomInterface(roomId, roomName, ownerId = null) {
  currentRoomId = roomId;
  currentRoomName = roomName;

  // `!= null` (нестрогое сравнение) ловит СРАЗУ и null, и undefined — то есть «значение не передали».
  // Обновляем владельца только если он реально пришёл, иначе оставляем прежний.
  if (ownerId != null) {
    currentRoomOwnerId = ownerId;
  }

  document.getElementById('roomInfo').classList.remove('hidden');
  document.getElementById('currentRoomName').textContent = roomName;

  document.getElementById('chatContainer').classList.remove('hidden');

  document.getElementById('rooms').classList.add('hidden');
  document.getElementById('connectBtn').classList.add('hidden');
  document.getElementById('createRoomBtn').classList.add('hidden');
  document.getElementById('startGameBtn').classList.remove('hidden');

  updateGameSettingsButton();
}

// Кнопку настроек показываем только владельцу комнаты.
// Это лишь UI-удобство: настоящая проверка прав живёт на бэке (вернёт 403 не-владельцу),
// поэтому даже если кнопка где-то мелькнёт не тому — сохранить настройки он всё равно не сможет.
function updateGameSettingsButton() {
  const btn = document.getElementById('gameSettingsBtn');
  if (!btn) return; // подстраховка: вдруг элемента нет в разметке

  const isOwner = currentRoomOwnerId != null && playerId === currentRoomOwnerId;

  // classList.toggle(class, force): при force=true класс добавляется, при false — убирается.
  // Здесь: если НЕ владелец -> добавить 'hidden' (спрятать), если владелец -> убрать.
  btn.classList.toggle('hidden', !isOwner);
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
  currentRoomOwnerId = null; // вышли из комнаты — забываем владельца

  resetGameUI();

  document.getElementById('roomInfo').classList.add('hidden');
  document.getElementById('chatContainer').classList.add('hidden');
  document.getElementById('startGameBtn').classList.add('hidden');
  document.getElementById('gameSettingsBtn').classList.add('hidden'); // прячем кнопку настроек

  document.getElementById('rooms').style.display = 'inline-block';
//  document.getElementById('createRoomBtn').style.display = 'inline-block';
  document.getElementById('createRoomBtn').classList.remove("hidden");

  document.getElementById('messages').innerHTML = '';
  document.getElementById('chatMessage').value = '';
}

function log(msg) {
  document.getElementById("log").textContent += msg + "\n";
}