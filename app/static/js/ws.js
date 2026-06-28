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
          console.log(data);

          if (data.event === 'round_started') {
            renderRound(data.round_data);

            const cardResponse = await fetch(`/player/${playerId}/cards`);
            const playerCards = await cardResponse.json();
            renderPlayerCards(playerCards);
            document.getElementById('playerCards').classList.remove('hidden');
          }

          if (data.event === 'player_selected_card') {
            console.log(data);
            renderCardBack(data); // data.event, data.card_id, data.image_url
          }

          if (data.event === 'player_joined_room') {
            currentRoomId = data.payload.room_id;
            localStorage.setItem("currentRoomId", currentRoomId);

            displaySystemMessage({
              message: `${data.payload.username} has joined the room`,
              timestamp: new Date().toISOString()
            });
          }

          if (data.event === "player_left_room") {
            displaySystemMessage({
              message: `${data.payload.username} has left the room.`,
              timestamp: new Date().toISOString()
            });
          }

          if (data.event === "player_reconnected") {
            const roomId = data.payload.room_id;
            const roomName = data.payload.room_name;
            avatar = data.payload.avatar;
            console.log('AVATART AFTER RECONNECT: ', avatar);

            reconnectToken = data.payload.reconnect_token;

            localStorage.setItem("playerId", playerId);
            localStorage.setItem("reconnectToken", reconnectToken);

            document.getElementById("createRoomBtn").disabled = false;
            document.getElementById('connectBtn').disabled = true;
            document.getElementById('startGameBtn').disabled = true;

            if ('room_id' in data.payload) {
              console.log('BEFORE SHOW_ROOM_INTERFACE');
                await showRoomInterface(roomId, roomName);
                console.log('AFTER SHOW_ROOM_INTERFACE');
                await loadChatHistory(roomId);
            }

            console.log('WS.JS LINE 72: ', data);
            loadProfile(data.payload.player_id);

            if ('game_state' in data.payload) {
              document.getElementById("playerCards").classList.remove("hidden");
              document.getElementById("tableArea").classList.remove("hidden");

              renderRound(data.payload);
              renderPlayerCards(data.payload.handed_cards);
            }

            if (!roomId) {
              await loadRooms();
            }
          }

          if (data.event === 'round_state_changed') {
            const state = data.payload.state;

            if (state === 'leader_choosing') {
              enterLeaderChoosingPhase();
            };

            if (state === 'round_ended') {
              exitLeaderChoosingPhase();
            };
          }

          if (data.event === 'first_round_started') {
            document.getElementById("playerCards").classList.remove("hidden");
            document.getElementById("tableArea").classList.remove("hidden");

            renderRound(data.payload);
            renderPlayerCards(data.payload.player_cards);
          }

          if (data.event === 'player_profile_updated') {
            document.querySelector("#username").textContent = data.username;
          }

          if (data.event === "player_created") {
            avatar = data.payload.avatar;
            playerId = data.payload.player_id;
            console.log(playerId);
            reconnectToken = data.payload.reconnect_token;

            localStorage.setItem("playerId", playerId);
            localStorage.setItem("reconnectToken", reconnectToken);

            document.getElementById("createRoomBtn").disabled = false;
            document.getElementById("connectBtn").disabled = true;

            loadProfile(data.payload.player_id);
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