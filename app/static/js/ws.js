    let ws;
    playerId = localStorage.getItem("playerId");
    let reconnectToken = localStorage.getItem("reconnectToken");
    currentRoomId = localStorage.getItem("currentRoomId");

    document.getElementById("connectBtn").addEventListener("click", () => {

      let wsUrl = "ws://localhost:8000/ws/";

      if (reconnectToken) {
        wsUrl += `?reconnect_token=${reconnectToken}`;
      };

      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        log("WS соединение установлено");
        loadRooms();
      };

      ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.event === 'room_state') {
            await handleRoomState(data.payload);
          }

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

          if (data.event === "room_joined") {
            currentRoomId = data.payload.room_id;
            localStorage.setItem("currentRoomId", currentRoomId);
          }

          if (data.event === "player_reconnected") {
            const roomId = data.payload.room_id;
            const roomName = data.payload.room_name;

            document.getElementById("createRoomBtn").disabled = false;
            document.getElementById('connectBtn').disabled = true;

            if (!roomId) {
              await loadRooms();
            }
          }

          if (data.event === "player_created") {
            playerId = data.payload.player_id;
            reconnectToken = data.payload.reconnect_token;

            localStorage.setItem("playerId", playerId);
            localStorage.setItem("reconnectToken", reconnectToken);

            document.getElementById("createRoomBtn").disabled = false;
            document.getElementById("connectBtn").disabled = true;
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