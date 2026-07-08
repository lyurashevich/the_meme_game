const scoreModal = document.querySelector("#scoreModal");
const scoreBtn = document.querySelector("#score");
const scoreList = document.querySelector("#scoreList");
const closeScoreBtn = document.querySelector("#closeScoreBtn")

scoreBtn.addEventListener("click", async () => {
  const players = await getGameScore(currentRoomId);
  renderScore(players);
  scoreModal.classList.remove("hidden");
});

closeScoreBtn.addEventListener("click", () => {
  scoreModal.classList.add("hidden");
});

function renderScore(players) {
  scoreList.innerHTML = "";

  for (const player of players) {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${player.username}</td>
      <td>${player.score}</td>
    `;

    scoreList.appendChild(row);
  }
}