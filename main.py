import sqlite3
import telebot
from telebot import types


class GameFinderBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.con = sqlite3.connect('TeamFiend.db', check_same_thread=False)

    def run(self):
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item_dota2 = types.KeyboardButton("Dota 2")
            item_cs2 = types.KeyboardButton("CS2")
            item_rust = types.KeyboardButton("Rust")
            markup.add(item_dota2, item_cs2, item_rust)

            self.bot.send_message(message.chat.id, "Привет! Давай начнем поиск напарников. Выбери игру:",
                                  reply_markup=markup)

        @self.bot.message_handler(func=lambda message: message.text.lower() in ["dota 2", "cs2", "rust"])
        def handle_game_selection(message):
            game = message.text.lower()
            user_id = message.from_user.id
            cur = self.con.cursor()
            cur_id = cur.execute('SELECT id FROM Games WHERE id = ? AND game = ?', (user_id, game)).fetchone()
            if cur_id is None:
                if game == "dota 2":
                    self.create_dota2_profile(message)
                else:
                    self.create_profile(message, game)
            else:
                if game == "dota 2":
                    self.show_random_profile(user_id, "dota 2")
                else:
                    self.show_random_profile(user_id, game)
                cur.close()

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_inline_buttons(call):
            user_id = call.from_user.id
            profile_id = int(call.data.split('_')[-2])
            game = call.data.split('_')[-1]
            if call.data.startswith("like"):
                liked_profile = self.get_profile_by_id(profile_id, game)
                if liked_profile:
                    if not self.check_if_already_liked(user_id, liked_profile):
                        self.send_matched_profiles(user_id, liked_profile)
                    else:
                        self.bot.answer_callback_query(call.id,
                                                       text="Вы уже лайкнули эту анкету. Нельзя лайкать одну анкету "
                                                            "дважды.",
                                                       show_alert=True)
            elif call.data.startswith("dislike"):
                self.show_random_profile(user_id, game)
            elif call.data.startswith("report"):
                self.ask_report_reason(user_id, profile_id)
            elif call.data.startswith("view_profile"):
                self.send_profile(user_id, self.get_profile_by_id(profile_id, game), game)
            elif call.data.startswith("skip_profile"):
                self.show_random_profile(user_id, game)
            elif call.data.startswith("back_to_rank"):
                self.create_dota2_profile(call.message)
            elif call.data.startswith("back_to_description"):
                self.bot.send_message(user_id, "Опишите себя:", reply_markup=types.ReplyKeyboardRemove())
                self.bot.register_next_step_handler(call.message, self.get_description, {'game': "dota 2"})
            elif call.data.startswith("back_to_game"):
                self.bot.send_message(user_id, "Выбери игру:",
                                      reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
                                      .add(types.KeyboardButton("Dota 2"),
                                           types.KeyboardButton("CS2"),
                                           types.KeyboardButton("Rust")))
            elif call.data.startswith("back_to_rank_selection"):
                self.create_dota2_profile(call.message)

        self.bot.polling(none_stop=True)

    def check_if_already_liked(self, user_id, liked_profile):
        cursor = self.con.cursor()
        cursor.execute('SELECT * FROM Matches WHERE user_id=? AND liked_user_id=? AND game=? LIMIT 1',
                       (user_id, liked_profile[1], liked_profile[0],))
        return cursor.fetchone() is not None

    def create_profile(self, message, game):
        user_id = message.from_user.id
        user_profile = {'game': game}
        self.bot.send_message(user_id, "Опишите себя:", reply_markup=types.ReplyKeyboardRemove())
        self.bot.register_next_step_handler(message, self.get_description, user_profile)

    def create_dota2_profile(self, message):
        user_id = message.from_user.id
        user_profile = {'game': "dota 2"}
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        rank_buttons = ["Рекрут", "Страж", "Рыцарь", "Герой", "Легенда", "Властелин", "Божество", "Титан"]
        for rank in rank_buttons:
            markup.add(types.KeyboardButton(rank))
        back_button = types.KeyboardButton("Назад")
        markup.add(back_button)
        self.bot.send_message(user_id, "Укажите ваш ранг в Dota 2:", reply_markup=markup)
        self.bot.register_next_step_handler(message, self.get_rank, user_profile)

    def get_rank(self, message, user_profile):
        user_id = message.from_user.id
        rank = message.text
        if rank not in ["Рекрут", "Страж", "Рыцарь", "Герой", "Легенда", "Властелин", "Божество", "Титан"]:
            self.bot.send_message(user_id, "Пожалуйста, выберите ранг из предложенных кнопок.")
            self.create_dota2_profile(message)
            return
        user_profile['rank'] = rank
        user_profile['tg_profile'] = message.from_user.username
        self.bot.send_message(user_id, "Опишите себя:", reply_markup=types.ReplyKeyboardRemove())
        self.bot.register_next_step_handler(message, self.get_description, user_profile)

    def get_description(self, message, user_profile):
        user_id = message.from_user.id
        user_profile['id'] = user_id
        user_profile['desc'] = message.text

        if user_profile['game'] == "dota 2":
            self.ask_for_search_criteria(message, user_profile)

    def ask_for_search_criteria(self, message, user_profile):
        user_id = message.from_user.id
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        goals = ["Рекрут-Страж", "Страж-Рыцарь", "Рыцарь-Герой", "Герой-Легенда", "Легенда-Властелин",
                 "Властелин-Божество", "Божество-Титан"]
        for goal in goals:
            markup.add(types.KeyboardButton(goal))
        back_button = types.KeyboardButton("Назад")
        markup.add(back_button)
        self.bot.send_message(user_id, "Выберите свои цели поиска:", reply_markup=markup)
        self.bot.register_next_step_handler(message, self.get_goals, user_profile)

    def get_goals(self, message, user_profile):
        user_id = message.from_user.id
        goals = message.text.split("-")
        user_profile['search_goal'] = "-".join(goals)  # Преобразуем список в строку для вставки в базу данных
        self.insert_profile(user_profile)
        self.show_random_profile(user_id, "dota 2")

    def insert_profile(self, user_profile):
        cur = self.con.cursor()
        try:
            sqlite_insert_query = """INSERT INTO Games
                                      (game, id, desc, tg_profile, rank, search_goal)
                                      VALUES
                                      (?, ?, ?, ?, ?, ?);"""
            column_values = (user_profile['game'], user_profile['id'], user_profile['desc'],
                             user_profile['tg_profile'], user_profile.get('rank', "Рекрут"),
                             user_profile.get('search_goal', "Рекрут-Страж"))
            cur.execute(sqlite_insert_query, column_values)
            self.con.commit()
        except Exception as e:
            print(user_profile)
            print(f"Failed to insert profile: {e}")
            self.con.rollback()
        cur.close()

    def show_random_profile(self, user_id, game):
        cursor = self.con.cursor()

        # Получаем данные о ранге и цели поиска текущего пользователя
        user_profile = cursor.execute('SELECT rank, search_goal FROM Games WHERE id = ? AND game = ?',
                                      (user_id, game)).fetchone()
        user_rank = user_profile[0]
        user_search_goal = user_profile[1]

        # Формируем запрос к базе данных с учетом ранга и цели поиска текущего пользователя
        if user_rank and user_search_goal:
            # Выбираем профили, учитывая ранг и цель поиска текущего пользователя
            cursor.execute('SELECT * FROM Games WHERE game = ? AND id != ? ORDER BY RANDOM()', (game, user_id))
            profiles = cursor.fetchall()

            # Фильтруем профили, чтобы оставить только те, которые соответствуют критериям поиска текущего пользователя
            valid_profiles = []
            for profile in profiles:
                # Проверяем соответствие ранга
                if profile[4] >= user_rank:  # Если ранг профиля больше или равен рангу пользователя
                    # Проверяем соответствие цели поиска
                    if user_search_goal in profile[5]:  # Если цель поиска пользователя входит в цели поиска профиля
                        valid_profiles.append(profile)

            # Если есть подходящие профили, 0выбираем случайный из них
            if valid_profiles:
                random_profile = random.choice(valid_profiles)
                self.send_profile(user_id, random_profile, game)
            else:
                self.bot.send_message(user_id, "Извините, но для Вас больше нет анкет.",
                                      reply_markup=types.ReplyKeyboardRemove())
        else:
            # Если у пользователя отсутствует ранг или цель поиска, просто выбираем случайный профиль
            cursor.execute('SELECT * FROM Games WHERE game = ? AND id != ? ORDER BY RANDOM() LIMIT 1', (game, user_id))
            random_profile = cursor.fetchone()
            cursor.close()

            if random_profile:
                self.send_profile(user_id, random_profile, game)
            else:
                self.bot.send_message(user_id, "Извините, но для Вас больше нет анкет.",
                                      reply_markup=types.ReplyKeyboardRemove())

    def send_profile(self, user_id, profile, game):
        description = profile[3]  # Поменяли индекс, так как порядок столбцов изменился в базе данных
        rank = profile[4]
        if rank:
            message_text = f"**Нашли для тебя подходящую анкету:**\n\n**Ранг:** {rank}\n**Описание:** {description}"
        else:
            message_text = f"**Нашли для тебя подходящую анкету:**\n\n**Описание:** {description}"
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        like_button = types.InlineKeyboardButton(text="Лайк", callback_data=f"like_{profile[1]}_{game}")
        dislike_button = types.InlineKeyboardButton(text="Пропустить", callback_data=f"dislike_{game}")
        report_button = types.InlineKeyboardButton(text="Report", callback_data=f"report_{profile[1]}_{game}")
        keyboard.add(like_button, dislike_button, report_button)
        self.bot.send_message(user_id, message_text, reply_markup=keyboard, parse_mode='Markdown')


if __name__ == "__main__":
    bot_token = ""  # Замените на ваш токен Telegram бота
    game_finder_bot = GameFinderBot(bot_token)
    game_finder_bot.run()
