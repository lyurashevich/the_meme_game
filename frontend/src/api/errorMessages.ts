// What to tell the player when an action fails. The server sends a machine-readable `code`
// and an English `message` meant for developers; the player gets a sentence picked by the code.
import { ActionError } from './GameSocket';

const MESSAGES: Record<string, string> = {
  // from the client itself (GameSocket)
  not_connected: 'Нет связи с сервером. Подождите, переподключаемся...',
  connection_lost: 'Связь прервалась, действие не выполнено. Попробуйте ещё раз',
  timeout: 'Сервер не ответил. Попробуйте ещё раз',

  // rooms
  room_not_found: 'Такой комнаты уже нет',
  room_is_full: 'В комнате нет свободных мест',
  game_already_started: 'В этой комнате уже идёт игра',
  already_in_a_room: 'Вы уже в другой комнате',
  username_taken: 'Это имя в комнате уже занято. Выберите другое',
  player_not_in_room: 'Вы не в комнате',
  not_room_owner_exception: 'Это может сделать только владелец комнаты',
  room_has_no_owner: 'У комнаты нет владельца, игру не начать',

  // game
  not_enough_players: 'Для игры нужно хотя бы 3 игрока',
  not_enough_cards: 'В колоде не хватает карт для стольких игроков',
  not_round_leader: 'Это может сделать только ведущий раунда',
  card_not_found: 'Этой карты уже нет',
  // The game moved on between the click and the server getting it (the timer ran out, say)
  invalid_game_state: 'Это действие сейчас недоступно',
  invalid_round_state: 'Это действие сейчас недоступно',
  invalid_player_action: 'Это действие сейчас недоступно',
  game_not_found: 'Игра уже закончилась',
  player_not_found: 'Игрок уже вышел из комнаты',
  round_not_found: 'Раунд уже закончился',

  // chat
  too_many_messages: 'Слишком много сообщений подряд. Подождите несколько секунд',

  // the request itself
  validation_error: 'Проверьте введённые данные',
  internal_error: 'На сервере что-то сломалось. Попробуйте ещё раз',
};

const FALLBACK = 'Что-то пошло не так. Попробуйте ещё раз';

export function describeError(error: unknown): string {
  if (error instanceof ActionError) {
    const text = MESSAGES[error.code];
    if (text) return text;
    // A code we don't know yet: worth a look, but the player still gets a readable sentence
    console.warn('No text for error code', error.code, error.message);
    return FALLBACK;
  }
  console.error(error); // not from the server: a bug on our side
  return FALLBACK;
}
