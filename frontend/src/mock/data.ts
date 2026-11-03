// Mock data shaped exactly like the server messages (see protocol.ts),
// so the screens won't need to change when they get real data.
import type { ChatMessage, MemeCard, RoomPlayer, RoomSummary, Session, Situation } from '../protocol';

export const MY_ID = 'p-me';

export const MOCK_SESSION: Session = {
  player_id: MY_ID,
  reconnect_token: 'mock-token',
  username: 'Кот_В_Шоке',
  avatar_id: 'cat',
};

export const MOCK_ROOMS: RoomSummary[] = [
  {
    id: 'room-1',
    name: 'Мемы после тяжелой недели 🍷',
    owner_name: 'Саня_Деплой',
    players_count: 5,
    max_players: 8,
    round_time_limit: 60,
    max_rounds: 5,
    status: 'waiting',
  },
  {
    id: 'room-2',
    name: 'Офисный планктон и выгорание ☕',
    owner_name: 'Татьяна_HR',
    players_count: 7,
    max_players: 8,
    round_time_limit: 90,
    max_rounds: null,
    status: 'waiting',
  },
  {
    id: 'room-3',
    name: 'Коты, которые знают слишком много',
    owner_name: 'Мяу_Мур',
    players_count: 4,
    max_players: 6,
    round_time_limit: 60,
    max_rounds: 10,
    status: 'playing',
  },
  {
    id: 'room-4',
    name: 'Постирония 5 уровня (без духоты)',
    owner_name: 'Кринж_Мастер',
    players_count: 3,
    max_players: 10,
    round_time_limit: 120,
    max_rounds: 10,
    status: 'waiting',
  },
  {
    id: 'room-5',
    name: 'Турнир: Главный мемный дед 🏆',
    owner_name: 'Олег_Ильич',
    players_count: 6,
    max_players: 6,
    round_time_limit: 90,
    max_rounds: 8,
    status: 'waiting',
  },
];

// Everyone in the mock room except you
export const MOCK_OTHER_PLAYERS: RoomPlayer[] = [
  { id: 'p2', username: 'Саня_Деплой', avatar_id: 'frog', score: 2, is_connected: true },
  { id: 'p3', username: 'Катя_Мем', avatar_id: 'capybara', score: 1, is_connected: true },
  { id: 'p4', username: 'Толян_Душнила', avatar_id: 'pigeon', score: 0, is_connected: false },
  { id: 'p5', username: 'Аня_Смешинка', avatar_id: 'hamster', score: 3, is_connected: true },
];

export const MOCK_SITUATION: Situation = {
  id: 42,
  text: 'Когда тимлид на общем созвоне спрашивает: «Ну что, кто вчера дропнул базу в проде?», а ты как раз жуешь бутерброд с выключенной камерой',
};

// Real cards are pictures from the media storage. Until there are any,
// draw simple ones in place: an SVG image encoded right into the URL.
function drawMeme(emoji: string, caption: string, background: string): string {
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300">` +
    `<rect width="300" height="300" fill="${background}"/>` +
    `<text x="150" y="130" font-size="120" text-anchor="middle" dominant-baseline="central">${emoji}</text>` +
    `<text x="150" y="262" font-size="24" font-weight="700" font-family="sans-serif" text-anchor="middle" fill="#242426">${caption}</text>` +
    `</svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

export const MOCK_HAND: MemeCard[] = [
  { id: 101, image_url: drawMeme('🐱', 'Я просто мимо проходил', '#EBE7DF') },
  { id: 102, image_url: drawMeme('🐸', 'План был надёжен', '#DFEAE2') },
  { id: 103, image_url: drawMeme('🦫', 'Полный дзен', '#EFE7D8') },
  { id: 104, image_url: drawMeme('🐹', 'Ой, а кто это сделал?!', '#F4E3DD') },
  { id: 105, image_url: drawMeme('🐶', 'Вау. Очень логично', '#F5ECD7') },
  { id: 106, image_url: drawMeme('🐦', 'Курлык?', '#E2E6EC') },
];

// Cards the other players put on the table, and who played each one.
// The server never tells who played what until the round is over - this is only for the mock.
export const MOCK_TABLE: { card: MemeCard; player_id: string }[] = [
  { card: { id: 201, image_url: drawMeme('🔥', 'Оно само сломалось!', '#F4E3DD') }, player_id: 'p2' },
  { card: { id: 202, image_url: drawMeme('🫠', 'Это не баг, это фича', '#DFEAE2') }, player_id: 'p3' },
  { card: { id: 203, image_url: drawMeme('🗿', 'Ничего не видел', '#E2E6EC') }, player_id: 'p5' },
];

export const MOCK_CHAT: ChatMessage[] = [
  {
    player_id: 'p2',
    username: 'Саня_Деплой',
    text: 'Ребята, ставьте самое абсурдное, я сегодня строгий ведущий 😎',
    timestamp: '2026-11-03T14:21:00Z',
  },
  {
    player_id: 'p3',
    username: 'Катя_Мем',
    text: 'У меня тут просто шедевр под эту ситуацию лежит, держитесь',
    timestamp: '2026-11-03T14:21:30Z',
  },
  {
    player_id: 'p4',
    username: 'Толян_Душнила',
    text: 'Вообще-то базу дропать нельзя без бэкапа по регламенту...',
    timestamp: '2026-11-03T14:22:00Z',
  },
  {
    player_id: 'p5',
    username: 'Аня_Смешинка',
    text: 'Толян, не душни в чате пжлст 🗿',
    timestamp: '2026-11-03T14:22:10Z',
  },
];
