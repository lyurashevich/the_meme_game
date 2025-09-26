function renderRound(round) {
  const container = document.getElementById("roundInfo");
  container.innerHTML = `
    <h2>Round #${round.round_number}</h2>
    <p>Leader: ${round.leader_id}</p>
    <p>Situation: ${round.situation_card_text}</p>
    <div class="choices">
      ${round.player_choices?.map(choice => `
        <div class="choice">
          <p>${choice.username}</p>
          ${choice.image_url}
        </div>
      `).join('') || '<p>Waiting for choices...</p>'}
    </div>
  `;
}

async function renderPlayerCards(cards) {
  const container = document.getElementById('cardsContainer');
  container.innerHTML = cards.map(card => `
    <div class="card" data-card-id="${card.id}">
      <img src="${card.image_url}" alt="Card">
    </div>
  `).join('');
}