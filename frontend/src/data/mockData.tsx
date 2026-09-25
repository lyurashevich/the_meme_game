import type { GameRoom, MemeCardData, SituationCardData, PlayerProfile, ChatMessage } from '../types';

export const INITIAL_ROOMS: GameRoom[] = [
  {
    id: 'room-1',
    name: 'Мемы после тяжелой недели 🍷',
    ownerName: 'Саня_Деплой',
    playersCount: 5,
    maxPlayers: 8,
    ownerId: "id",
    roundsCount: 5,
    timeLimit: 60,
    isPrivate: false,
    // status: 'waiting',
  },
  {
    id: 'room-2',
    name: 'Офисный планктон и выгорание ☕',
    ownerName: 'Татьяна_HR',
    playersCount: 7,
    maxPlayers: 8,
    ownerId: "id",
    roundsCount: 7,
    timeLimit: 45,
    isPrivate: false,
    // status: 'waiting',
  },
  {
    id: 'room-3',
    name: 'Коты, которые знают слишком много',
    ownerName: 'Мяу_Мур',
    playersCount: 4,
    maxPlayers: 6,
    ownerId: "id",
    roundsCount: 5,
    timeLimit: 60,
    isPrivate: false,
    // status: 'waiting',
  },
  {
    id: 'room-4',
    name: 'Постирония 5 уровня (без духоты)',
    ownerName: 'Кринж_Мастер',
    playersCount: 3,
    maxPlayers: 8,
    ownerId: "id",
    roundsCount: 10,
    timeLimit: 30,
    isPrivate: false,
    // status: 'waiting',
  },
  {
    id: 'room-5',
    name: 'Турнир: Главный мемный дед 🏆',
    ownerName: 'Олег_Ильич',
    playersCount: 6,
    maxPlayers: 6,
    ownerId: "id",
    roundsCount: 8,
    timeLimit: 45,
    isPrivate: false,
    // status: 'full',
  },
];

export const CURRENT_SITUATION: SituationCardData = {
  id: 'sit-42',
  // category: 'Жизненный дедлайн',
  roundNumber: 2,
  prompt: 'Когда тимлид на общем созвоне спрашивает: «Ну что, кто вчера дропнул базу в проде?», а ты как раз в этот момент жуешь бутерброд с выключенной камерой',
  submittedCardsCount: 4,
};

export const MOCK_HAND_CARDS: MemeCardData[] = [
  {
    id: 'card-1',
    title: '«Я просто мимо проходил»',
    caption: 'Лицо абсолютной невиновности и легкой паники',
    memeType: 'cat',
    flavorText: 'Пушистый алиби не требует доказательств',
    colorTheme: '#EBE7DF',
  },
  {
    id: 'card-2',
    title: '«План был надежен, как швейцарские часы»',
    caption: 'Когда за 5 минут до созвона переписал половину логики',
    memeType: 'frog',
    flavorText: 'Осталось молиться на кеш',
    colorTheme: '#DFEAE2',
  },
  {
    id: 'card-3',
    title: '«Полное спокойствие и дзен»',
    caption: 'Сгорел сарай — гори и хата',
    memeType: 'capybara',
    flavorText: 'Апельсин на макушке стабилизирует психику',
    colorTheme: '#EFE7D8',
  },
  {
    id: 'card-4',
    title: '«Ой, а кто это сделал?!»',
    caption: 'Внутренний монолог в момент фатального энтера',
    memeType: 'hamster',
    flavorText: 'Глаза размером с Луну',
    colorTheme: '#F4E3DD',
  },
  {
    id: 'card-5',
    title: '«Вау. Очень логично. Много смысла»',
    caption: 'Мой ответ на вопрос: "А зачем ты это нажал?"',
    memeType: 'doge',
    flavorText: 'Экспертная аналитика высочайшего класса',
    colorTheme: '#F5ECD7',
  },
];

export const PLAYED_TABLE_CARDS: {
  id: string;
  playerId: string;
  playerName: string;
  avatarId: string;
  isRevealed: boolean;
  card: MemeCardData;
  position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  votesCount?: number;
}[] = [
  {
    id: 'play-1',
    playerId: 'p2',
    playerName: 'Саня_Деплой',
    avatarId: 'frog',
    isRevealed: true,
    card: {
      id: 'card-rev-1',
      title: '«Оно само сломалось!»',
      caption: 'Когда открыл консоль, а там красный водопад ошибок',
      memeType: 'frog',
      flavorText: 'Я просто чихнул рядом с сервером',
      colorTheme: '#DFEAE2',
    },
    position: 'top-left',
    votesCount: 2,
  },
  {
    id: 'play-2',
    playerId: 'p3',
    playerName: 'Катя_Мем',
    avatarId: 'cat',
    isRevealed: false,
    card: {
      id: 'card-rev-2',
      title: 'Секретный мем',
      caption: 'Катя выбрала свой козырь',
      memeType: 'cat',
      colorTheme: '#EBE7DF',
    },
    position: 'top-right',
  },
  {
    id: 'play-3',
    playerId: 'p4',
    playerName: 'Толян_Душнила',
    avatarId: 'pigeon',
    isRevealed: false,
    card: {
      id: 'card-rev-3',
      title: 'Секретный мем',
      caption: 'Мем завёрнут в постиронию',
      memeType: 'pigeon',
      colorTheme: '#E2E6EC',
    },
    position: 'bottom-left',
  },
  {
    id: 'play-4',
    playerId: 'p-me',
    playerName: 'Вы (Игрок)',
    avatarId: 'capybara',
    isRevealed: true,
    card: {
      id: 'card-1',
      title: '«Я просто мимо проходил»',
      caption: 'Лицо абсолютной невиновности и легкой паники',
      memeType: 'cat',
      flavorText: 'Ваш выбор в этом раунде',
      colorTheme: '#EBE7DF',
    },
    position: 'bottom-right',
    votesCount: 1,
  },
];

export const MOCK_PLAYERS_IN_ROOM: PlayerProfile[] = [
  {
    id: 'p-me',
    username: 'Вы (Игрок)',
    avatarId: 'capybara',
    isConnected: true,
  },
  {
    id: 'p2',
    username: 'Саня_Деплой',
    avatarId: 'frog',
    isConnected: true,
  },
  {
    id: 'p3',
    username: 'Катя_Мем',
    avatarId: 'cat',
    isConnected: true,
  },
  {
    id: 'p4',
    username: 'Толян_Душнила',
    avatarId: 'pigeon',
    isConnected: true,
  },
  {
    id: 'p5',
    username: 'Аня_Смешинка',
    avatarId: 'hamster',
    isConnected: true,
  },
];

export const MOCK_CHAT_MESSAGES: ChatMessage[] = [
  {
    id: 'm1',
    sender: 'Система',
    avatarId: 'system',
    text: 'Раунд 2 начался! Тема: Жизненный дедлайн',
    time: '14:20',
    isSystem: true,
  },
  {
    id: 'm2',
    sender: 'Саня_Деплой',
    avatarId: 'frog',
    text: 'Ребята, ставьте самое абсурдное, я сегодня строгий ведущий 😎',
    time: '14:21',
  },
  {
    id: 'm3',
    sender: 'Катя_Мем',
    avatarId: 'cat',
    text: 'У меня тут просто шедевр под эту ситуацию лежит, держитесь',
    time: '14:21',
  },
  {
    id: 'm4',
    sender: 'Толян_Душнила',
    avatarId: 'pigeon',
    text: 'Вообще-то базу дропать нельзя без бэкапа по регламенту ГОСТ 7.1...',
    time: '14:22',
  },
  {
    id: 'm5',
    sender: 'Аня_Смешинка',
    avatarId: 'hamster',
    text: 'Толян, не душни в чате пжлст 🗿',
    time: '14:22',
  },
];
