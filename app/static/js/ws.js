    let ws;
    playerId = localStorage.getItem("playerId");
    let reconnectToken = localStorage.getItem("reconnectToken");
    let pendingPhase = null;
    let isAnimating = false;

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

//          ==============ROOM EVENTS==============

          if (data.event === 'room_created') {
            document.getElementById("createRoomBtn").classList.add("hidden");
            currentRoomId = data.payload.room_id;
            currentRoomName = data.payload.room_name;

            addRoomToList(currentRoomId, currentRoomName)
          }

          if (data.event === 'room_deleted') {

          }

          if (data.event === 'room_updated') {

          }

//          ===============PLAYER EVENTS==============

          if (data.event === 'player_joined_room') {
            displaySystemMessage({
              message: `${data.payload.username} has joined the room`,
              timestamp: new Date().toISOString()
            });
          }

          if (data.event === 'you_joined_the_room') {
            currentRoomId = data.payload.room_id;
            currentRoomName = data.payload.room_name;
            localStorage.setItem("currentRoomId", currentRoomId);

            document.getElementById("createRoomBtn").classList.add("hidden");

            await showRoomInterface(currentRoomId, currentRoomName);
            await loadChatHistory(currentRoomId);
          }

          if (data.event === "player_left_room") {
            displaySystemMessage({
              message: `${data.payload.username} has left the room.`,
              timestamp: new Date().toISOString()
            });
          }

          if (data.event === 'you_left_the_room') {
            document.getElementById("createRoomBtn").classList.remove("hidden");
            currentRoomId = null;
          }

          if (data.event === "player_reconnected") {
            const roomId = data.payload.room_id;
            const roomName = data.payload.room_name;
            avatar = data.payload.avatar;

            reconnectToken = data.payload.reconnect_token;

            localStorage.setItem("playerId", playerId);
            localStorage.setItem("reconnectToken", reconnectToken);

            if (!roomId) {
              document.getElementById("createRoomBtn").classList.remove("hidden");
            }

            document.getElementById('connectBtn').disabled = true;
            document.getElementById('startGameBtn').disabled = true;

            if ('room_id' in data.payload) {
                await showRoomInterface(roomId, roomName);
                await loadChatHistory(roomId);
            }

            loadProfile(data.payload.player_id);

            if ('game_state' in data.payload) {
              document.getElementById("playerCards").classList.remove("hidden");
              document.getElementById("tableArea").classList.remove("hidden");

              renderRound(data.payload);
              renderPlayerCards(data.payload.handed_cards);
              renderPlayedCards(data.payload.players_choice);
            }

            if (!roomId) {
              await loadRooms();
            }
          }

          if (data.event === "round_started") {
            console.log('WS.JS LINE 114 DATA = ', data);
            renderRound(data.payload);
            renderPlayerCards(data.payload.player_cards);

            if (!isLeader) {
              confirmChoiceBtn.classList.remove("hidden");
            }
          }

//          if (data.event === 'round_started') {
//            renderRound(data.round_data);
//
//            const cardResponse = await fetch(`/player/${playerId}/cards`);
//            const playerCards = await cardResponse.json();
//            renderPlayerCards(playerCards);
//            document.getElementById('playerCards').classList.remove('hidden');
//          }

          if (data.event === 'player_selected_card') {
            renderCardBack(data); // data.event, data.card_id, data.image_url
          }

          if (data.event === 'player_card_removed') {
            const cardId = data.payload && data.payload.card_id;
            const card = document.querySelector(`.played-card[data-card-id="${cardId}"]`);
            if (card) {
              card.remove();
              if (cardsReceived > 0) cardsReceived--;
            }
          }

          if (data.event === 'round_state_changed') {
            const state = data.payload.state;

            if (state === 'leader_choosing') {
              pendingPhase = state;
              confirmChoiceBtn.classList.add("hidden");

              tryApplyPhase();
            };

            if (state === 'round_ended') {
              exitLeaderChoosingPhase();
              clearTable();
            };
          }

          if (data.event === 'game_started') {

            currentRoomId = data.payload.room_id;
            scoreBtn.classList.remove("hidden");

            document.getElementById("startGameBtn").classList.add("hidden");
            document.getElementById("playerCards").classList.remove("hidden");
            document.getElementById("tableArea").classList.remove("hidden");

//            renderRound(data.payload);
//            renderPlayerCards(data.payload.player_cards);
//
//            if (!isLeader) {
//              confirmChoiceBtn.classList.remove("hidden");
//            }
          }

          if (data.event === 'game_ended') {
            displaySystemMessage({
              message: data.payload && data.payload.message ? data.payload.message : "Игра завершена.",
              timestamp: new Date().toISOString()
            });

            resetGameUI();
            document.getElementById("startGameBtn").classList.remove("hidden");
          }

          if (data.event === 'player_profile_updated') {
            document.querySelector("#username").textContent = data.username;
          }

          if (data.event === "player_created") {
            avatar = data.payload.avatar;
            playerId = data.payload.player_id;
            reconnectToken = data.payload.reconnect_token;

            localStorage.setItem("playerId", playerId);
            localStorage.setItem("reconnectToken", reconnectToken);

            document.getElementById("createRoomBtn").classList.remove("hidden");
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