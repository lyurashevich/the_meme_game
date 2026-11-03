import { Loader2, X } from 'lucide-react';
import { useState } from 'react';
import { ActionError } from './api/GameSocket';
import AppHeader from './components/AppHeader';
import ConnectionIndicator from './components/ConnectionIndicator';
import DesignSpecsModal from './components/DesignSpecsModal';
import GameResultsModal from './components/GameResultsModal';
import GameScreen from './screens/GameScreen';
import LobbyScreen from './screens/LobbyScreen';
import PlayerCreationScreen from './screens/PlayerCreationScreen';
import RoomListScreen from './screens/RoomListScreen';
import { useGameStore } from './store/gameStore';

// Whether this tab has been through the profile screen; per tab, like the player itself
const PROFILE_KEY = 'profile_confirmed';

export default function App() {
  // One selector per field: App re-renders when one of these changes, not on every change in the store
  const me = useGameStore((state) => state.me);
  const rooms = useGameStore((state) => state.rooms);
  const roomState = useGameStore((state) => state.roomState);
  const gameEnded = useGameStore((state) => state.gameEnded);
  // The actions are created once with the store and never change, so no subscription is needed
  const actions = useGameStore.getState();

  const [profileConfirmed, setProfileConfirmed] = useState(() => sessionStorage.getItem(PROFILE_KEY) === 'yes');
  const [showSpecs, setShowSpecs] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const confirmProfile = (confirmed: boolean) => {
    sessionStorage.setItem(PROFILE_KEY, confirmed ? 'yes' : 'no');
    setProfileConfirmed(confirmed);
  };

  // Until there are proper notifications, a refused action shows up as a strip at the top
  const showError = (reason: unknown) => {
    if (reason instanceof ActionError) {
      setError(reason.message);
    } else {
      console.error(reason);
      setError('Что-то пошло не так');
    }
  };

  // Run an action and report a failure; the screens don't need to know about errors at all
  const run =
    <Args extends unknown[]>(action: (...args: Args) => Promise<unknown>) =>
    (...args: Args) => {
      setError(null);
      action(...args).catch(showError);
    };

  const leaveRoom = async () => {
    try {
      // During a game the server asks to confirm first, since leaving costs the player their place
      const { requires_confirmation } = await actions.leaveRoom();
      if (requires_confirmation && window.confirm('Игра идёт. Точно выйти? Вернуться в эту игру уже не получится.')) {
        await actions.leaveRoom(true);
      }
    } catch (reason) {
      showError(reason);
    }
  };

  // The screen follows from the state. A player who reconnects into a room goes straight back to it.
  let content;
  if (!me) {
    content = <ConnectingScreen />;
  } else if (roomState?.game) {
    content = (
      <GameScreen
        me={me}
        roomState={roomState}
        game={roomState.game}
        onSelectCard={run(actions.selectCard)}
        onChooseWinner={run(actions.chooseWinner)}
        onSendMessage={run(actions.sendChat)}
        onLeaveRoom={leaveRoom}
        onEndGame={run(actions.endGame)}
      />
    );
  } else if (roomState) {
    content = (
      <LobbyScreen
        me={me}
        roomState={roomState}
        onStartGame={run(actions.startGame)}
        onLeaveRoom={leaveRoom}
        onUpdateSettings={run(actions.updateSettings)}
        onSendMessage={run(actions.sendChat)}
      />
    );
  } else if (!profileConfirmed) {
    content = (
      <PlayerCreationScreen me={me} onSaveProfile={actions.updateProfile} onConfirm={() => confirmProfile(true)} />
    );
  } else {
    content = (
      <RoomListScreen
        me={me}
        rooms={rooms}
        onJoinRoom={run(actions.joinRoom)}
        onCreateRoom={run(actions.createRoom)}
        onEditProfile={() => confirmProfile(false)}
      />
    );
  }

  // Results belong to the room the player is in; after leaving it they are no longer shown
  const results = gameEnded && roomState?.room.id === gameEnded.room_id ? gameEnded : null;

  return (
    <div className="min-h-screen bg-[#F4F1EA] text-[#242426] flex flex-col font-['Rubik',sans-serif]">
      <AppHeader onShowSpecs={() => setShowSpecs(true)} />

      {error && (
        <div role="alert" className="border-b-2 border-[#242426] bg-[#E8BAA8] px-4 py-2">
          <div className="max-w-7xl mx-auto flex items-center justify-between gap-3 text-xs font-bold text-[#52291E]">
            <span>{error}</span>
            <button onClick={() => setError(null)} aria-label="Закрыть" className="cursor-pointer">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      <main className="flex-1">{content}</main>

      {results && me && roomState && (
        <GameResultsModal
          results={results}
          players={roomState.players}
          myId={me.player_id}
          onClose={actions.dismissGameResults}
        />
      )}
      <DesignSpecsModal isOpen={showSpecs} onClose={() => setShowSpecs(false)} />
      <ConnectionIndicator />
    </div>
  );
}

// Until the server has told us who we are, there is nothing to show
function ConnectingScreen() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 min-h-[calc(100vh-65px)] text-sm font-bold text-[#55524B]">
      <Loader2 className="w-8 h-8 animate-spin" />
      Подключаемся к серверу...
    </div>
  );
}
