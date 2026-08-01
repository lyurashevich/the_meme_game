// ownerId прилетает из списка комнат (loadRooms), где /room/all уже отдаёт owner_id.
// Прокидываем его дальше в showRoomInterface, чтобы тот решил, показывать ли кнопку настроек.
async function joinRoom(roomId, roomName, ownerId = null) {
  try {
    const response = await fetch(`/room/${roomId}`, {
      method: "PATCH",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        player_id: playerId,
        room_id: roomId
      })
    });

    if (response.ok) {
      currentRoomId = roomId;
      document.getElementById('chatContainer').classList.remove('hidden');
      await showRoomInterface(roomId, roomName, ownerId);
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
      div.className = "room-card";
      // Передаём room.owner_id третьим аргументом: так после входа мы сразу знаем владельца
      // и можем правильно показать/скрыть кнопку настроек.
      div.innerHTML = `
        <p class="room-card__name">${room.name} <span class="room-card__count">${room.players_count}/${room.max_players}</span></p>
        <button class="btn btn-primary btn-pill" onclick="joinRoom('${room.id}', '${room.name}', '${room.owner_id}')">Join room</button>
      `;
      container.appendChild(div);
    });
  } catch (error) {
    log("error: " + error);
  }
}

function saveSettings() {
  const newName = document.querySelector('#settingsUsername').value;
  updateUsername(newName);
}

async function updateUsername(newName) {
  const res = await fetch(`/player/${playerId}/profile`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: newName })
  });

  const data = await res.json();
  document.querySelector("#username").textContent = data.username;
}

document.querySelector('#saveSettingsBtn').addEventListener('click', () => {
  saveSettings();
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

function isSettingsOpen() {
  return !modal.classList.contains('hidden');
}

document.addEventListener('keydown', (event) => {
  if (!isSettingsOpen()) return;

  if (event.key === 'Escape') {
    modal.classList.add('hidden');
  }

  if (event.key === 'Enter') {
    saveSettings();
    modal.classList.add('hidden');
  }
});

avatar.addEventListener("click", () => {
  modal.classList.remove("hidden");

  document.querySelector("#settingsUsername").value =
    document.querySelector("#username").textContent;
});

document.querySelector("#closeSettingsBtn").addEventListener("click", () => {
  modal.classList.add("hidden");
});

async function getGameScore(roomId) {
  const response = await fetch(`/game/${roomId}/score`);

  if (!response.ok) {
    console.log("Failed to get score");
  }

  result = await response.json();

  return result;
}


/* ==========================================================================
   НАСТРОЙКИ ИГРЫ (game settings)
   Поток: владелец жмёт "Game settings" -> openGameSettings() подтягивает
   текущие настройки с сервера и открывает модалку -> владелец меняет ->
   saveGameSettings() отправляет их на сервер (PUT).
   ========================================================================== */

// Сервер отдаёт ошибки в ДВУХ разных форматах, и их надо разбирать по-разному:
//   1) наши доменные ошибки (403 не владелец, 404 нет комнаты):
//        { "error": { "code": "...", "message": "..." } }
//   2) ошибки валидации Pydantic (422, например round_time_limit = 45):
//        { "detail": [ { "msg": "...", "loc": [...] }, ... ] }
// Эта функция вытаскивает человекочитаемый текст из любого из них.
async function extractErrorMessage(response) {
  // .catch(() => ({})) — если тело пустое или не JSON, не падаем, а берём пустой объект.
  const body = await response.json().catch(() => ({}));

  if (body.error && body.error.message) {
    return body.error.message;                       // формат (1) — доменная ошибка
  }
  if (Array.isArray(body.detail)) {
    return body.detail.map(e => e.msg).join("; ");    // формат (2) — 422, собираем все msg
  }
  if (typeof body.detail === "string") {
    return body.detail;                               // иногда detail — просто строка
  }
  return `Error ${response.status}`;                  // на всё остальное — код статуса
}

// Кладём значения настроек в поля формы (префилл).
function fillGameSettingsForm(settings) {
  // У <select> значение всегда строка, поэтому число приводим к строке через String().
  document.getElementById("settingRoundTime").value = String(settings.round_time_limit);

  // `??` (nullish coalescing): вернёт правую часть ТОЛЬКО если левая null или undefined.
  // Здесь: null (безлимит) показываем как пустое поле "", а не как текст "null".
  document.getElementById("settingMaxRounds").value = settings.max_rounds ?? "";
  document.getElementById("settingScoreToWin").value = settings.score_to_win ?? "";
}

// Читаем значения из формы и собираем объект в том виде, который ждёт бэк.
function readGameSettingsForm() {
  const roundTime = Number(document.getElementById("settingRoundTime").value);

  // .trim() убирает случайные пробелы. Пустая строка означает "безлимит" -> null.
  const maxRoundsRaw = document.getElementById("settingMaxRounds").value.trim();
  const scoreRaw = document.getElementById("settingScoreToWin").value.trim();

  return {
    round_time_limit: roundTime,
    max_rounds: maxRoundsRaw === "" ? null : Number(maxRoundsRaw),
    score_to_win: scoreRaw === "" ? null : Number(scoreRaw),
  };
}

async function openGameSettings() {
  if (!currentRoomId) return; // не в комнате — открывать нечего

  // Значения по умолчанию на случай, если настройки ещё не удастся получить.
  const defaults = { round_time_limit: 60, max_rounds: null, score_to_win: null };

  try {
    // GET текущих настроек для префилла.
    const response = await fetch(`/game/${currentRoomId}/game_settings`);

    if (response.ok) {
      const settings = await response.json();
      fillGameSettingsForm(settings);
    } else {
      // Эндпоинта пока нет / комната не найдена — не блокируем UI, показываем дефолты.
      log("Could not load settings: " + await extractErrorMessage(response));
      fillGameSettingsForm(defaults);
    }
  } catch (error) {
    // Сюда попадаем при сетевой ошибке (сервер недоступен и т.п.).
    log("Network error while loading settings: " + error);
    fillGameSettingsForm(defaults);
  }

  // Показываем модалку (снимаем класс hidden).
  document.getElementById("gameSettingsModal").classList.remove("hidden");
}

async function saveGameSettings() {
  if (!currentRoomId || !playerId) return;

  const settings = readGameSettingsForm();

  try {
    const response = await fetch(`/game/${currentRoomId}/game_settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      // Тело строго по схеме UpdateGameSettingsRequest: player_id + вложенный объект settings.
      body: JSON.stringify({ player_id: playerId, settings }),
    });

    if (!response.ok) {
      // 403 (не владелец), 404 (нет комнаты/игры), 422 (невалидные значения) — все сюда.
      alert("Failed to save settings: " + await extractErrorMessage(response));
      return;
    }

    // Сервер возвращает применённые настройки — синхронизируем форму с "правдой" сервера.
    const saved = await response.json();
    fillGameSettingsForm(saved);
    log("Settings saved: " + JSON.stringify(saved));

    document.getElementById("gameSettingsModal").classList.add("hidden");
  } catch (error) {
    alert("Network error while saving settings: " + error);
  }
}

// Навешиваем обработчики один раз при загрузке скрипта.
// Скрипты подключены в конце <body>, поэтому элементы уже существуют в DOM.
document.getElementById("gameSettingsBtn").addEventListener("click", openGameSettings);
document.getElementById("saveGameSettingsBtn").addEventListener("click", saveGameSettings);
document.getElementById("closeGameSettingsBtn").addEventListener("click", () => {
  document.getElementById("gameSettingsModal").classList.add("hidden");
});
