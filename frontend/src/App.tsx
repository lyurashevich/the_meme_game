import { useState } from 'react';
import DesignSpecsModal from './components/DesignSpecsModal';
import MockControls from './components/MockControls';
import MockupHeader from './components/MockupHeader';
import { useMockServer } from './mock/useMockServer';
import GameScreen from './screens/GameScreen';
import LobbyScreen from './screens/LobbyScreen';
import PlayerCreationScreen from './screens/PlayerCreationScreen';
import RoomListScreen from './screens/RoomListScreen';
import type { ScreenId } from './types';

export default function App() {
  const server = useMockServer(); // will be replaced by the WebSocket store
  const { me, roomState } = server;
  const [profileConfirmed, setProfileConfirmed] = useState(false);
  const [showSpecs, setShowSpecs] = useState(false);

  // The screen isn't stored anywhere: it follows from the state
  const screen: ScreenId = !profileConfirmed
    ? 'screen1'
    : !roomState
      ? 'screen2'
      : !roomState.game
        ? 'screen3'
        : 'screen4';

  // Mockup header: jumping to a screen means putting the state into the matching shape
  const goToScreen = (target: ScreenId) => {
    setProfileConfirmed(target !== 'screen1');
    if (target === 'screen2') server.leaveRoom();
    if (target === 'screen3') server.mock.showLobby(true);
    if (target === 'screen4') server.mock.showGame('choosing_cards', false);
  };

  let content;
  if (screen === 'screen1') {
    content = (
      <PlayerCreationScreen
        me={me}
        onUpdateProfile={server.updateProfile}
        onConfirm={() => setProfileConfirmed(true)}
      />
    );
  } else if (!roomState) {
    content = (
      <RoomListScreen
        me={me}
        rooms={server.rooms}
        onJoinRoom={server.joinRoom}
        onCreateRoom={server.createRoom}
        onEditProfile={() => setProfileConfirmed(false)}
      />
    );
  } else if (!roomState.game) {
    content = (
      <LobbyScreen
        me={me}
        roomState={roomState}
        onStartGame={server.startGame}
        onLeaveRoom={server.leaveRoom}
        onUpdateSettings={server.updateSettings}
        onSendMessage={server.sendChat}
      />
    );
  } else {
    content = (
      <GameScreen
        me={me}
        roomState={roomState}
        game={roomState.game}
        onSelectCard={server.selectCard}
        onChooseWinner={server.chooseWinner}
        onSendMessage={server.sendChat}
        onLeaveRoom={server.leaveRoom}
        onEndGame={server.endGame}
      />
    );
  }

  return (
    <div className="min-h-screen bg-[#F4F1EA] text-[#242426] flex flex-col font-['Rubik',sans-serif]">
      <MockupHeader currentScreen={screen} onSelectScreen={goToScreen} onToggleSpecs={() => setShowSpecs(true)} />
      {profileConfirmed && roomState && <MockControls myId={me.player_id} roomState={roomState} mock={server.mock} />}

      <main className="flex-1">{content}</main>

      <DesignSpecsModal isOpen={showSpecs} onClose={() => setShowSpecs(false)} />
    </div>
  );
}
