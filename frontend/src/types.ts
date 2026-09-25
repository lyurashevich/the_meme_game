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
  username: string;
  avatarId: string;
  isConnected: boolean;
}

export interface GameRoom {
  id: string;
  name: string;
  ownerName: string;
  playersCount: number;
  maxPlayers: number;
  ownerId: string;
  invitationLink?: string;
  roundsCount: number;
  timeLimit: number;
  isPrivate: boolean;
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
  // category: string;
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
