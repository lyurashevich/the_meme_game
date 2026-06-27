let leaderChoosingPhaseInitialized = false;
let selectedWinnerCardId = null;

function enterLeaderChoosingPhase () {
  if (leaderChoosingPhaseInitialized) {
    return;
  }

  leaderChoosingPhaseInitialized = true;

  const playedCards = document.querySelectorAll('.played-card');
  playedCards.forEach((card, index) => {
    card.classList.add('revealed');
  });

  if (isLeader) {
    attachWinnerSelectionHandler();
    document.getElementById('confirmWinner').classList.remove('hidden');
  }
}

function attachWinnerSelectionHandler () {
  const playedCards = document.querySelectorAll('.played-card');

  playedCards.forEach(card => {
    card.addEventListener('click', handlePlayedCardClick);
  });
}

async function handlePlayedCardClick(event) {
  const card = event.currentTarget;
  selectedWinnerCardId = card.dataset.cardId;

  document.querySelectorAll('.played-card').forEach(c => {
    c.classList.remove('selected-for-winner');
  });
  card.classList.add('selected-for-winner');
}

function exitLeaderChoosingPhase() {
  leaderChoosingPhaseInitialized = false;

  document.querySelectorAll('.played-card').forEach(card => {
    card.classList.remove('selected-for-winner');
  });

  document.getElementById('confirmWinner').classList.add('hidden');
  selectedWinnerCardId = null;
}


function renderRound(payload) {
  const container = document.getElementById('roundInfo');
  container.innerHTML = `
    <h2>Round #${payload.current_round_number}</h2>
    <p>Leader: ${payload.leader_id}</p>
    <p>Situation: ${payload.current_situation_card.text}</p>
  `;

  updateLeaderStatus(payload.leader_id);
  console.log('GAME.JS LINE 91: IS_LEADER = ', isLeader);
}

async function renderPlayerCards(cards) {
  const container  = document.getElementById('cardsContainer');
  container.innerHTML = cards.map(card => `
    <div class="card" data-card-id="${card.id}">
      <img src="${card.image_url}" alt="Card">
    </div>
  `).join('');
}

async function animateCardToCenter(cardElement) {
  const img = cardElement.querySelector('img');

  if (img) {
    img.style.display = 'none';
  }

  cardElement.style.background = 'darkslateblue';

  const table = document.getElementById("tableArea");
  const cardRect = cardElement.getBoundingClientRect();
  const tableRect = table.getBoundingClientRect();

  cardElement.classList.add("flying");

  cardElement.style.left = `${cardRect.left}px`;
  cardElement.style.top = `${cardRect.top}px`;

  cardElement.offsetHeight;

  cardElement.style.left = `${tableRect.left + tableRect.width / 2 - cardRect.width / 2}px`;
  cardElement.style.top = `${tableRect.top + tableRect.height / 2 - cardRect.height / 2}px`;

  cardElement.style.transform = "scale(0.8)";

  return new Promise(resolve => {
    cardElement.addEventListener(
      "transitionend",
      resolve,
      { once: true }
      );
  });
}

function renderCardBack(data) {
  const table = document.getElementById('tableArea');

  table.innerHTML += `
    <div class="played-card" data-card-id="${data.card_id}">
      <img src="${data.image_url}" alt="Card">
    </div>
  `;
}
