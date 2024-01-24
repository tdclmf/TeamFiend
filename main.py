import telebot
from telebot import types
import sqlite3
import random


class GameFinderBot:
    def __init__(self, token):
        self.search_goals = ["Рекрут-Страж", "Страж-Рыцарь", "Рыцарь-Герой", "Герой-Легенда", "Легенда-Властелин",
                             "Властелин-Божество", "Божество-Титан", "Титан"]
        self.ranks = ["Рекрут", "Страж", "Рыцарь", "Герой", "Легенда", "Властелин", "Божество", "Титан"]
        self.bot = telebot.TeleBot(token)
        self.admins = ['admin1_id', 'admin2_id']
        self.user_profiles = {}
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

        @self.bot.message_handler(func=lambda message: message.text == "Dota 2")
        def handle_dota2(message):
            user_id = message.from_user.id
            cur = self.con.cursor()
            cur_id = cur.execute('SELECT id FROM Games WHERE id = ? AND game = ?', (user_id, "Dota 2")).fetchone()
            try:
                if user_id != cur_id[0]:
                    self.create_profile(message, "Dota 2")
                else:
                    search_goal = \
                        cur.execute('SELECT search_goal FROM Games WHERE id=? AND game = ?', (user_id, "Dota 2",)).fetchone()[0]
                    rank = cur.execute('SELECT rank FROM Games WHERE id=? AND game = ?', (user_id, "Dota 2",)).fetchone()[0]
                    self.show_random_profile(message, "Dota 2", search_goal, rank)
            except TypeError as e:
                print(e)
                self.create_profile(message, "Dota 2")

        # ... другие обработчики для CS2 и Rust ...

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_inline_buttons(call):
            user_id = call.from_user.id
            profile_id = int(call.data.split('_')[-2])
            if call.data[1].startswith("like"):
                liked_profile = self.get_profile_by_id(profile_id, call.data[1])
                if liked_profile:
                    self.send_matched_profiles(user_id, liked_profile)
            elif call.data[1].startswith("dislike"):
                self.show_random_profile(message=call.message, game=call.data[1], search_goal=call.data[2],
                                         rank=call.data[3])
            elif call.data.startswith("report"):
                self.ask_report_reason(user_id, profile_id)

        self.bot.polling(none_stop=True)

    def create_profile(self, message, game):
        user_id = message.from_user.id
        user_profile = {'game': game}
        self.bot.send_message(user_id, "Опишите себя и свою цель поиска:", reply_markup=types.ReplyKeyboardRemove())
        self.bot.register_next_step_handler(message, self.get_description, user_profile)

    def get_description(self, message, user_profile):
        user_id = message.from_user.id
        user_profile['id'] = user_id
        user_profile['description'] = message.text
        self.bot.send_message(user_id, "Теперь укажите свой ID в Telegram:")
        self.bot.register_next_step_handler(message, self.get_telegram_id, user_profile)

    def get_telegram_id(self, message, user_profile):
        user_id = message.from_user.id
        if message.text.startswith("@"):
            user_profile['telegram_id'] = message.text
            self.bot.send_message(user_id, "Выберите свой ранг:", reply_markup=self.get_rank_keyboard())
            self.bot.register_next_step_handler(message, self.get_rank, user_profile)
        else:
            self.bot.send_message(user_id, "id должен начинаться с, помните, что ненастоящий id"
                                           "приведёт к блокировке аккаунта в боте.")
            self.bot.register_next_step_handler(message, self.get_telegram_id, user_profile)

    def get_rank_keyboard(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for rank in self.ranks:
            markup.add(types.KeyboardButton(rank))
        return markup

    def get_rank(self, message, user_profile):
        user_id = message.from_user.id
        if message.text in self.ranks:
            user_profile['rank'] = message.text
            self.bot.send_message(user_id, "Выберите цель поиска:", reply_markup=self.get_search_goal_keyboard())
            self.bot.register_next_step_handler(message, self.get_search_goal, user_profile)
        else:
            self.bot.send_message(user_id, "Кажется, такого варианта нет...")
            self.bot.register_next_step_handler(message, self.get_rank, user_profile)

    def get_search_goal_keyboard(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for goal in self.search_goals:
            markup.add(types.KeyboardButton(goal))
        return markup

    def get_search_goal(self, message, user_profile):
        user_id = message.from_user.id
        if message.text in self.search_goals:
            user_profile['search_goal'] = message.text
            self.bot.send_message(user_id, "Анкета создана! Теперь вы можете начать поиск напарников.",
                                  reply_markup=types.ReplyKeyboardRemove())
            print(user_profile)
            print(tuple(user_profile.values()))
            cur = self.con.cursor()
            try:
                sqlite_insert_query = """INSERT INTO Games
                                          (game, id, desc, username, rank, search_goal)
                                          VALUES
                                          (?, ?, ?, ?, ?, ?);"""
                column_values = (tuple(user_profile.values()))
                cur.execute(sqlite_insert_query, column_values)
                self.con.commit()
            except Exception as e:
                print(e)
                self.con.rollback()
            cur.close()
            self.show_random_profile(message, user_profile["game"], user_profile["search_goal"], user_profile["rank"])
        else:
            self.bot.send_message(user_id, "Кажется, такого варианта нет...")
            self.bot.register_next_step_handler(message, self.get_search_goal, user_profile)

    def get_random_profile(self, user_id, game, search_goal, rank):
        cursor = self.con.cursor()
        search_goal = search_goal.split("-")
        ranks = {"Рекрут": "Рекрут-Страж",
                 "Страж": ["Рекрут-Страж", "Страж-Рыцарь"],
                 "Рыцарь": ["Страж-Рыцарь", "Рыцарь-Герой"],
                 "Герой": ["Рыцарь-Герой", "Герой-Легенда"],
                 "Легенда": ["Герой-Легенда", "Герой-Властелин"],
                 "Властелин": ["Легенда-Властелин", "Властелин-Божество"],
                 "Божество": ["Властелин-Божество", "Божество-Титан"],
                 "Титан": ["Божество-Титан", "Титан"]}
        cur_rank = ranks[rank]
        cursor.execute('SELECT * FROM Games WHERE game = ? '
                       'AND id != ? AND (rank = ? OR rank = ?) AND (search_goal = ? OR search_goal = ?) ORDER BY '
                       'RANDOM() LIMIT 1',
                       (game, user_id, search_goal[0], search_goal[1], cur_rank[0], cur_rank[1],))
        return cursor.fetchone()

    def show_random_profile(self, message, game, search_goal, rank):
        user_id = message.from_user.id
        random_profile = self.get_random_profile(user_id, game, search_goal, rank)
        print(random_profile)
        if random_profile:
            self.send_profile(message.chat.id, random_profile, game)
        else:
            self.bot.send_message(user_id, "Извините, но анкеты для поиска закончились.")

    def send_profile(self, chat_id, profile, game):
        user_id = profile[1]  # ID пользователя
        description = profile[2]
        rank = profile[4]
        print(rank)
        game = game

        keyboard = types.InlineKeyboardMarkup(row_width=2)
        like_button = types.InlineKeyboardButton(text="Лайк", callback_data=f"like_{user_id}_{game}")
        dislike_button = types.InlineKeyboardButton(text="Дизлайк", callback_data=f"dislike_{user_id}_{game}")
        report_button = types.InlineKeyboardButton(text="Report", callback_data=f"report_{user_id}_{game}")

        keyboard.add(like_button, dislike_button, report_button)

        if rank in self.ranks:
            message_text = f"**Описание:** {description}\n**Ранг:** {rank}"
        else:
            message_text = f"**Описание:** {description}"

        self.bot.send_message(chat_id, message_text, reply_markup=keyboard, parse_mode='Markdown')

    def get_profile_by_id(self, profile_id, game):
        cursor = self.con.cursor()
        cursor.execute('SELECT * FROM ? WHERE game=? LIMIT 1', (game, profile_id,))
        return cursor.fetchone()

    def send_matched_profiles(self, user_id, liked_profile):
        pass
        # Логика для отправки сообщения с совпавшими анкетами
        # Этот метод вызывается, если пользователи лайкнули друг друга

    def ask_report_reason(self, user_id, reported_profile_id):
        pass
        # Логика для запроса причины жалобы и отправки ее администраторам


if __name__ == "__main__":
    bot_token = ""
    game_finder_bot = GameFinderBot(bot_token)
    game_finder_bot.run()
