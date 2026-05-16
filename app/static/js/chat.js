function displayChatMessage(data) {
  const messagesContainer = document.getElementById('messages');
  const messageElement = document.createElement('div');
  messageElement.className = 'message';

  const time = new Date(data.timestamp).toLocaleTimeString();
  messageElement.innerHTML = `
    <span class="message-sender">${data.player_name || 'Anonymous'}:</span>
    <span>${data.message}</span>
    <span class="message-time">${time}</span>
  `;

  messagesContainer.appendChild(messageElement);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function displaySystemMessage(data) {
  const messagesContainer = document.getElementById('messages');
  const messageElement = document.createElement('div');
  messageElement.className = 'message system-message';

  const time = new Date(data.timestamp).toLocaleTimeString();
  messageElement.innerHTML = `
    <span>${data.message}</span>
    <span class="message-time">${time}</span>
  `;

  messagesContainer.appendChild(messageElement);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function loadChatHistory(roomId) {
  try {
    const response = await fetch(`/room/${roomId}/messages`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const messages = await response.json();

    if (!Array.isArray(messages)) {
      console.warn('Messages is not an array:', messages);
      return;
    }

    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '';

    messages.forEach(message => {
      displayChatMessage(message);
    });
  } catch (error) {
    console.error('Error load chat history:', error);
  }
}