    let ws;

    document.getElementById("connectBtn").addEventListener("click", () => {
      ws = new WebSocket("ws://localhost:8000/ws/");

      ws.onopen = () => {
        log("WS соединение установлено");
        loadRooms();
      };

      ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.event === 'round_started') {
            renderRound(data.round_data);

            const cardResponse = await fetch(`/player/${playerId}/cards`);
            const playerCards = await cardResponse.json();
            renderPlayerCards(playerCards);
            document.getElementById('playerCards').classList.remove('hidden');
          }

          if (data.event === 'player_joined') {
            displaySystemMessage({
              message: `${data.data.username} has joined the room`,
              timestamp: new Date().toISOString()
            });
          }

          if (data.event === "player_created") {
            playerId = data.player_id;
//            log("Создан игрок с id: " + playerId);
            document.getElementById("createRoomBtn").disabled = false;
        } else if (data.event == 'chat_message') {
          if (currentRoomId && data.room_id === currentRoomId) {
            displayChatMessage(data);
          }
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    };

      ws.onclose = () => log("WS соединение закрыто");
      ws.onerror = (error) => log("ws error: " + error);
    });