import { useState } from 'react';
import DesignSpecsModal from './components/DesignSpecsModal';
import MockupHeader from './components/MockupHeader';
import PlayerCreationScreen from './screens/PlayerCreationScreen';
import type { PlayerProfile, ScreenId } from './types';

// Mock data until the app talks to the server
const MOCK_PLAYER: PlayerProfile = {
  id: 'p-me',
  username: 'Кот_В_Шоке',
  avatarId: 'cat',
  isConnected: true,
};

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<ScreenId>('screen1');
  const [showSpecs, setShowSpecs] = useState(false);
  const [player, setPlayer] = useState<PlayerProfile>(MOCK_PLAYER);

  const updatePlayer = (changes: Partial<PlayerProfile>) => {
    setPlayer((current) => ({ ...current, ...changes }));
  };

  return (
    <div className="min-h-screen bg-[#F4F1EA] text-[#242426] flex flex-col font-['Rubik',sans-serif]">
      <MockupHeader
        currentScreen={currentScreen}
        onSelectScreen={setCurrentScreen}
        onToggleSpecs={() => setShowSpecs(true)}
      />

      <main className="flex-1">
        {currentScreen === 'screen1' ? (
          <PlayerCreationScreen
            player={player}
            onUpdatePlayer={updatePlayer}
            onConfirm={() => setCurrentScreen('screen2')}
          />
        ) : (
          <NotPortedYet screen={currentScreen} />
        )}
      </main>

      <DesignSpecsModal isOpen={showSpecs} onClose={() => setShowSpecs(false)} />
    </div>
  );
}

// Placeholder for the screens that are still being moved over from the Vue mockup
function NotPortedYet({ screen }: { screen: ScreenId }) {
  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-65px)] p-6">
      <div className="rounded-3xl border-2 border-dashed border-[#242426]/40 bg-[#ECE8DE] px-6 py-4 text-sm font-bold text-[#55524B]">
        Экран «{screen}» ещё переносится с Vue на React
      </div>
    </div>
  );
}
