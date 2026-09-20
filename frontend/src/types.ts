export interface AvatarOption {
  id: string;
  name: string;
  mood: string;
  tag: string;
  bgColor: string;
  accentColor: string;
}

export interface PlayerProfile {
  id: string;
  nickname: string;
  avatarId: string;
  isHost?: boolean;
  score?: number;
  status?: string;
  isReady?: boolean;
  hasPlayedCard?: boolean;
}

export interface GameRoom {
  id: string;
  name: string;
  // hostName: string;
  playersCount: number;
  maxPlayers: number;
  ownerId: str;
  invitationLink?: string;
  // roundsCount: number;
  // timeLimit: number;
  // tag: string;
  isPrivate?: boolean;
  // status: 'waiting' | 'in-progress' | 'full';
}

export interface MemeCardData {
  id: string;
  title: string;
  imageUrl?: string;
  caption: string;
  memeType: 'cat' | 'doge' | 'frog' | 'capybara' | 'hamster' | 'pigeon';
  flavorText?: string;
  colorTheme?: string;
}

export interface SituationCardData {
  id: string;
  category: string;
  roundNumber: number;
  prompt: string;
  submittedCardsCount?: number;
}

export interface ChatMessage {
  id: string;
  sender: string;
  avatarId: string;
  text: string;
  time: string;
  isSystem?: boolean;
}

export type ScreenId = 'screen1' | 'screen2' | 'screen3' | 'screen4';
