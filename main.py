import telebot
from telebot import types
import sqlite3
import random
from Determinations import Determination
import time
import datetime


def get_view_profile_keyboard(user_id, game):
    keyboard = types.InlineKeyboardMarkup()
    view_profile_button = types.InlineKeyboardButton(text="Посмотреть профиль",
                                                     callback_data=f"view_profile_{user_id}_{game}")
    skip_profile_button = types.InlineKeyboardButton(text="Пропустить", callback_data=f"skip_profile_{user_id}_{game}")
    for i in [view_profile_button, skip_profile_button]:
        keyboard.add(i)
    return keyboard


def get_profile_actions_keyboard(game):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    edit_button = types.KeyboardButton(f"Редактировать профиль {game}")
    delete_button = types.KeyboardButton(f"Удалить профиль {game}")
    search_button = types.KeyboardButton(f"Начать поиск {game}")
    for i in [edit_button, delete_button, search_button]:
        keyboard.add(i)
    return keyboard


def get_dota_edits_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    desc = types.KeyboardButton(f"Описание")
    rank = types.KeyboardButton(f"Ранг")
    search = types.KeyboardButton(f"Целевые ранги")
    keyboard.add(desc, rank, search)
    return keyboard


def get_desc_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back = types.KeyboardButton("Вернуться")
    kb.add(back)
    return kb


def log_action(user_id, action):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} - User {user_id}: {action}\n")
    with open("bot_logs.txt", "a") as log_file:
        log_file.write(f"{timestamp} - User {user_id}: {action}\n")


def is_rules_accepted(user_id):
    con = sqlite3.connect('TeamFiend.db', check_same_thread=False)
    cur = con.cursor().execute("SELECT user_id FROM accepted_rules WHERE user_id=?", (user_id,))
    return cur.fetchone() is not None


def add_user_to_accepted_rules(user_id):
    con = sqlite3.connect('TeamFiend.db', check_same_thread=False)
    try:
        con.cursor().execute("INSERT INTO accepted_rules (user_id) VALUES (?)", (user_id,))
        con.commit()
    except Exception:
        return


class GameFinderBot:
    def __init__(self, token):
        deter = Determination()
        self.last_button_click = {}
        self.search_goals = deter.search_goals
        self.ranks = deter.ranks
        self.bot = telebot.TeleBot(token)
        self.admins = deter.admins
        self.con = sqlite3.connect('TeamFiend.db', check_same_thread=False)

    def run(self):

        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            if not is_rules_accepted(message.from_user.id):
                self.not_accept(message)
                return
            if not self.is_user_banned(message.from_user.id):
                log_action(message.from_user.id, "/start command executed")
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item_dota2 = types.KeyboardButton("Dota 2")
                item_cs2 = types.KeyboardButton("CS2")
                item_rust = types.KeyboardButton("Rust")
                markup.add(item_dota2, item_cs2, item_rust)
                markup.add(types.KeyboardButton("Brawl Stars"))
                self.bot.send_message(message.chat.id, "Привет! Давай начнем поиск напарников. Выбери игру:",
                                      reply_markup=markup)

        @self.bot.message_handler(func=lambda message: message.text == "Редактировать профиль Dota 2")
        def handle_edit_dota2_profile(message):
            if not is_rules_accepted(message.from_user.id):
                self.not_accept(message)
                return
            if not self.is_user_banned(message.from_user.id):
                self.edit_profile(message, "dota 2")

        @self.bot.message_handler(func=lambda message: message.text == "Удалить профиль Dota 2")
        def handle_delete_dota2_profile(message):
            if not is_rules_accepted(message.from_user.id):
                self.not_accept(message)
                return
            if not self.is_user_banned(message.from_user.id):
                self.delete_profile(message, "dota 2")

        @self.bot.message_handler(func=lambda message: message.text == "Редактировать профиль CS2")
        def handle_edit_cs2_profile(message):
            if not is_rules_accepted(message.from_user.id):
                self.not_accept(message)
                return
            if not self.is_user_banned(message.from_user.id):
                self.edit_profile(message, "CS2")

        @self.bot.message_handler(func=lambda message: message.text == "Удалить профиль CS2")
        def handle_delete_cs2_profile(message):
            if not is_rules_accepted(message.from_user.id):
                self.not_accept(message)
                return
            if not self.is_user_banned(message.from_user.id):
                self.delete_profile(message, "CS2")

        @self.bot.message_handler(func=lambda message: message.text == "Редактировать профиль Rust")
        def handle_edit_rust_profile(message):
            if not is_rules_accepted(message.from_user.id):
                not_accept(message)
                return
            if not self.is_user_banned(message.from_user.id):
                self.edit_profile(message, "Rust")

        @self.bot.message_handler(func=lambda message: message.text == "Удалить профиль Rust")
        def handle_delete_rust_profile(message):
            if not is_rules_accepted(message.from_user.id):
                self.not_accept(message)
                return
            if not self.is_user_banned(message.from_user.id):
                self.delete_profile(message, "Rust")

        @self.bot.message_handler(func=lambda message: message.text == "Начать поиск Dota 2")
        def start_search_dota(message):
            user_id = message.from_user.id
            if not is_rules_accepted(user_id):
                self.not_accept(message)
                return
            if not self.is_user_banned(user_id):
                cur = self.con.cursor()
                search_goal = \
                    cur.execute('SELECT search_goal FROM Games WHERE id=? AND game = ?',
                                (user_id, "dota 2",)).fetchone()[0]
                rank = cur.execute('SELECT rank FROM Games WHERE id=? AND game = ?',
                                   (user_id, "dota 2",)).fetchone()[0]
                cur.close()
                self.bot.send_message(message.from_user.id, "Секунду...", reply_markup=types.ReplyKeyboardRemove())
                self.show_random_profile(message, "dota 2", search_goal, rank)

        @self.bot.message_handler(func=lambda message: message.text == "Начать поиск CS2")
        def start_search_cs(message):
            if not is_rules_accepted(message.from_user.id):
                self.not_accept(message)
                return
            if not self.is_user_banned(message.from_user.id):
                self.bot.send_message(message.from_user.id, "Секунду...", reply_markup=types.ReplyKeyboardRemove())
                self.show_random_profile(message, "CS2", None, None)

        @self.bot.message_handler(func=lambda message: message.text == "Начать поиск Rust")
        def start_search_rust(message):
            if not self.is_user_banned(message.from_user.id):
                self.bot.send_message(message.from_user.id, "Секунду...", reply_markup=types.ReplyKeyboardRemove())
                self.show_random_profile(message, "Rust", None, None)

        @self.bot.message_handler(func=lambda message: message.text == "Начать поиск Brawl Stars")
        def start_search_brawl(message):
            if not self.is_user_banned(message.from_user.id):
                self.bot.send_message(message.from_user.id, "Секунду...", reply_markup=types.ReplyKeyboardRemove())
                self.show_random_profile(message, "Brawl Stars", None, None)

        @self.bot.message_handler(func=lambda message: message.text == "Dota 2")
        def handle_dota2(message):
            user_id = message.from_user.id
            if not is_rules_accepted(user_id):
                self.not_accept(message)
                return
            if not self.is_user_banned(user_id):
                log_action(message.from_user.id, "Handling Dota 2")
                cur = self.con.cursor()
                cur_id = cur.execute('SELECT id FROM Games WHERE id = ? AND game = ?', (user_id, "dota 2")).fetchone()
                cur.close()
                try:
                    if cur_id[0]:
                        self.bot.send_message(message.chat.id, "Выберите действие:",
                                              reply_markup=get_profile_actions_keyboard("Dota 2"))
                    else:
                        self.create_profile(message, "dota 2")
                except TypeError:
                    self.create_profile(message, "dota 2")

        @self.bot.message_handler(func=lambda message: message.text == "CS2")
        def handle_cs2(message):
            user_id = message.from_user.id
            if not is_rules_accepted(user_id):
                self.not_accept(message)
                return
            if not self.is_user_banned(user_id):
                cur = self.con.cursor()
                cur_id = cur.execute('SELECT id FROM Games WHERE id = ? AND game = ?', (user_id, "CS2")).fetchone()
                try:
                    if user_id != cur_id[0]:
                        self.create_profile(message, "CS2")
                    else:
                        if cur_id[0]:
                            self.bot.send_message(message.chat.id, "Выберите действие:",
                                                  reply_markup=get_profile_actions_keyboard("CS2"))
                        cur.close()
                except TypeError:
                    self.create_profile(message, "CS2")

        @self.bot.message_handler(func=lambda message: message.text == "Rust")
        def handle_rust(message):
            user_id = message.from_user.id
            if not is_rules_accepted(user_id):
                self.not_accept(message)
                return
            if not self.is_user_banned(user_id):
                cur = self.con.cursor()
                cur_id = cur.execute('SELECT id FROM Games WHERE id = ? AND game = ?', (user_id, "Rust")).fetchone()
                try:
                    if user_id != cur_id[0]:
                        self.create_profile(message, "Rust")
                    else:
                        self.bot.send_message(message.chat.id, "Выберите действие:",
                                              reply_markup=get_profile_actions_keyboard("Rust"))
                        cur.close()
                except TypeError:
                    self.create_profile(message, "Rust")

        @self.bot.message_handler(func=lambda message: message.text == "Brawl Stars")
        def handle_brawl_stars(message):
            user_id = message.from_user.id
            if not is_rules_accepted(user_id):
                self.not_accept(message)
                return
            if not self.is_user_banned(user_id):
                cur = self.con.cursor()
                cur_id = cur.execute('SELECT id FROM Games WHERE id = ? AND game = ?',
                                     (user_id, "Brawl Stars")).fetchone()
                try:
                    if user_id != cur_id[0]:
                        self.create_profile(message, "Brawl Stars")
                    else:
                        self.bot.send_message(message.chat.id, "Выберите действие:",
                                              reply_markup=get_profile_actions_keyboard("Brawl Stars"))
                        cur.close()
                except TypeError:
                    self.create_profile(message, "Brawl Stars")

        @self.bot.message_handler(func=lambda message: message.text == "Редактировать профиль Brawl Stars")
        def handle_edit_brawl_profile(message):
            if not is_rules_accepted(message.from_user.id):
                not_accept(message)
                return
            if not self.is_user_banned(message.from_user.id):
                print(123)
                self.edit_profile(message, "Brawl Stars")

        @self.bot.message_handler(func=lambda message: message.text == "Удалить профиль Brawl Stars")
        def handle_delete_brawl_profile(message):
            if not is_rules_accepted(message.from_user.id):
                self.not_accept(message)
                return
            if not self.is_user_banned(message.from_user.id):
                self.delete_profile(message, "Brawl Stars")

        @self.bot.message_handler(commands=['ban'])
        def handle_ban(message):
            if message.from_user.id in self.admins:
                if len(message.text.split()) == 2:
                    user_id = message.text.split()[1]
                    self.ban_user(user_id)
                    self.bot.reply_to(message, f"Пользователь с ID {user_id} был заблокирован.")
                else:
                    self.bot.reply_to(message, "Вы забыли указать ID пользователя после команды /ban.")

        @self.bot.message_handler(commands=['unban'])
        def handle_unban(message):
            if message.from_user.id in self.admins:
                if len(message.text.split()) == 2:
                    user_id = message.text.split()[1]
                    self.unban_user(user_id)
                    self.bot.reply_to(message, f"Пользователь с ID {user_id} был разблокирован.")
                else:
                    self.bot.reply_to(message, "Вы забыли указать ID пользователя после команды /unban.")

        @self.bot.callback_query_handler(func=lambda call: call.data == "accept_rules")
        def accept_rules_callback(call):
            if not is_rules_accepted(call.from_user.id):
                self.bot.answer_callback_query(call.id, "")
                user_id = call.from_user.id
                add_user_to_accepted_rules(user_id)
                self.bot.send_message(call.message.chat.id, "Вы успешно приняли правила. Теперь вы можете использовать "
                                                            "бота. Нажмите /start")
            else:
                self.bot.answer_callback_query(call.id,
                                               text="Вы уже согласились с нашими правилами. Приятного пользования!",
                                               show_alert=True)

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_inline_buttons(call):
            user_id = call.from_user.id
            if not is_rules_accepted(user_id):
                self.not_accept(message)
                return
            if not self.is_user_banned(user_id):
                current_time = time.time()
                cur = self.con.cursor()
                if user_id in self.last_button_click and current_time - self.last_button_click[user_id] < 3:
                    self.bot.answer_callback_query(call.id,
                                                   text="Подождите немного перед следующим нажатием кнопки.",
                                                   show_alert=True)
                    return
                self.last_button_click[user_id] = current_time
                profile_id = int(call.data.split('_')[-2])
                if call.data.startswith("like"):
                    cur_res = cur.execute('SELECT * FROM Games WHERE id = ? AND game = ?',
                                          (user_id, call.data.split('_')[-1])).fetchone()
                    cur.close()
                    liked_profile = self.get_profile_by_id(profile_id, call.data.split('_')[-1])
                    print(call.data)
                    if liked_profile:
                        if not self.check_if_already_liked(user_id, liked_profile):
                            self.send_matched_profiles(user_id, liked_profile)
                            self.show_random_profile(message=call.message, game=call.data.split('_')[-1],
                                                     search_goal=cur_res[5],
                                                     rank=cur_res[4])
                            self.bot.answer_callback_query(call.id, "")
                        else:
                            self.bot.answer_callback_query(call.id,
                                                           text="Вы уже лайкнули эту анкету. Нельзя лайкать одну анкету"
                                                                "дважды.",
                                                           show_alert=True)
                elif call.data.startswith("dislike"):
                    cur_res = cur.execute('SELECT * FROM Games WHERE id = ? AND game = ?',
                                          (user_id, call.data.split('_')[-1])).fetchone()
                    cur.close()
                    self.show_random_profile(message=call.message, game=call.data.split('_')[-1],
                                             search_goal=cur_res[5],
                                             rank=cur_res[4])
                    self.bot.answer_callback_query(call.id, "")
                elif call.data.startswith("report"):
                    self.ask_report_reason(user_id, profile_id)
                    self.bot.answer_callback_query(call.id, "")
                elif call.data.startswith("view_profile"):
                    user_id_to_view = int(call.data.split('_')[-2])
                    game_to_view = call.data.split('_')[-1]
                    self.send_profile(call.message.chat.id, self.get_profile_by_id(user_id_to_view, game_to_view),
                                      game_to_view)
                    self.bot.answer_callback_query(call.id, "")
                elif call.data.startswith("skip_profile"):
                    res = cur.execute('SELECT * FROM Games WHERE id = ? AND game = ?',
                                      (user_id, call.data.split('_')[-1])).fetchone()
                    self.show_random_profile(message=call.message, game=call.data.split('_')[-1],
                                             search_goal=(res[5] if len(res) == 6 else None),
                                             rank=(res[4] if len(res) == 6 else None))
                    self.bot.answer_callback_query(call.id, "")

        e = None
        while True:
            try:
                if e:
                    for i in self.admins:
                        self.bot.send_message(i, f"Произошла ошибка!\n{e}")
                        e = None
                self.bot.polling(none_stop=True)
            except Exception as e:
                try:
                    print(e)
                    time.sleep(3)
                except Exception:
                    time.sleep(3)

    def ban_user(self, user_id):
        if not self.is_user_banned(user_id):
            self.bot.send_message(user_id, "Вы были заблокированы в боте.")
            cur = self.con.cursor()
            cur.executescript(f"INSERT INTO BannedUsers (user_id) VALUES ({user_id});"
                              f"DELETE FROM Matches WHERE user_id={user_id};"
                              f"DELETE FROM Games WHERE id={user_id};")
            self.con.commit()
            cur.close()

    def unban_user(self, user_id):
        if self.is_user_banned(user_id):
            cursor = self.con.cursor()
            cursor.execute("DELETE FROM BannedUsers WHERE user_id=?", (user_id,))
            self.con.commit()
            cursor.close()
            self.bot.send_message(user_id, "Ваше блокировка в боте была снята. "
                                           "Вам необходимо заново создать свои профили!")

    def is_user_banned(self, user_id):
        cursor = self.con.cursor()
        cursor.execute("SELECT * FROM BannedUsers WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        return result is not None

    def check_if_already_liked(self, user_id, liked_profile):
        cursor = self.con.cursor()
        cursor.execute('SELECT * FROM Matches WHERE user_id=? AND liked_user_id=? AND game=? LIMIT 1',
                       (user_id, liked_profile[1], liked_profile[0],))
        return cursor.fetchone() is not None

    def create_profile(self, message, game):
        user = message.from_user
        user_id = user.id
        if not self.is_user_banned(user_id):
            if user.username:
                log_action(message.from_user.id, "Creating profile")
                user_profile = {'game': game}
                self.bot.send_message(user_id, "Опишите себя и свою цель поиска:", reply_markup=get_desc_kb())
                self.bot.register_next_step_handler(message, self.get_description, user_profile)
            else:
                self.bot.send_message(user_id, "Для использования бота, необходимо добавить на свой аккаунт username, "
                                               "это можно сделать в настройках. Затем создайте аккаунт заново, нажав на"
                                               "команду /start")

    def get_description(self, message, user_profile):
        user_id = message.from_user.id
        if not self.is_user_banned(user_id):
            log_action(message.from_user.id, "Getting description")
            if message.text == "Вернуться":
                self.returned(message)
                return
            if message.text and len(message.text) <= 4000:
                user_profile['id'] = user_id
                user_profile['description'] = message.text
                user_id = message.from_user.id
                user = message.from_user
                user_profile['username'] = user.username
                if user_profile['game'] == "dota 2":
                    self.bot.send_message(user_id, "Выберите свой ранг:", reply_markup=self.get_rank_keyboard())
                    self.bot.register_next_step_handler(message, self.get_rank_dota, user_profile)
                else:
                    cur = self.con.cursor()
                    try:
                        sqlite_insert_query = """INSERT INTO Games
                                                    (game, id, desc, tg_profile)
                                                    VALUES
                                                    (?, ?, ?, ?);"""
                        column_values = (tuple(user_profile.values()))
                        cur.execute(sqlite_insert_query, column_values)
                        self.con.commit()
                    except Exception:
                        self.con.rollback()
                    cur.close()
                    self.show_random_profile(message, user_profile["game"], None, None)
            else:
                self.bot.send_message(user_id, "Это не текстовое сообщение или сообщение более 4000 символов...")
                self.bot.send_message(user_id, "Опишите себя и свою цель поиска:")
                self.bot.register_next_step_handler(message, self.get_description, user_profile)

    def edit_profile(self, message, game):
        user_id = message.from_user.id
        if not self.is_user_banned(user_id):
            if message.text == "Вернуться":
                self.returned(message)
                return
            if game == "dota 2":
                self.bot.send_message(user_id, "Что вы хотите изменить в своем профиле?",
                                      reply_markup=get_dota_edits_keyboard())
                self.bot.register_next_step_handler(message, self.choice, game)
            else:
                self.bot.send_message(user_id, "Введите новое описание:", reply_markup=get_desc_kb())
                self.bot.register_next_step_handler(message, self.edit_profile_description, game)


    def choice(self, message, game):
        user_id = message.from_user.id
        if not self.is_user_banned(user_id):
            if message.text == "Описание":
                self.bot.send_message(user_id, "Введите новое описание:", reply_markup=get_desc_kb())
                self.bot.register_next_step_handler(message, self.edit_profile_description, game)
            if message.text == "Ранг":
                self.bot.send_message(user_id, "Выберите новый ранг:", reply_markup=self.get_rank_keyboard())
                self.bot.register_next_step_handler(message, self.edit_dota_rank)
            if message.text == "Целевые ранги":
                self.bot.send_message(user_id, "Выберите новые целевые ранги:",
                                      reply_markup=self.get_search_goal_keyboard())
                self.bot.register_next_step_handler(message, self.edit_dota_search_goal)

    def edit_profile_description(self, message, game):
        user_id = message.from_user.id
        if not self.is_user_banned(user_id):
            if message.text and len(message.text) <= 4000:
                if message == "Вернуться":
                    self.returned(message)
                    return
                new_description = message.text
                cur = self.con.cursor()
                cur.execute("UPDATE Games SET desc=? WHERE id=? AND game=?", (new_description, user_id, game,))
                self.con.commit()
                cur.close()
                self.bot.send_message(user_id, "Профиль успешно обновлен.", reply_markup=types.ReplyKeyboardRemove())
            else:
                self.bot.send_message(user_id, "Это не текстовое сообщение или сообщение более 4000 символов...")
                self.bot.send_message(user_id, "Опишите себя и свою цель поиска:")
                self.bot.register_next_step_handler(message, self.edit_profile_description, user_profile)

    def edit_dota_rank(self, message):
        user_id = message.from_user.id
        if not self.is_user_banned(user_id):
            if message.text in self.ranks:
                new_rank = message.text
                cur = self.con.cursor()
                cur.execute("UPDATE Games SET rank=? WHERE id=? AND game=?", (new_rank, user_id, "dota 2",))
                self.con.commit()
                cur.close()
                self.bot.send_message(user_id, "Профиль успешно обновлен.", reply_markup=types.ReplyKeyboardRemove())
            else:
                return self.edit_dota_rank(message)

    def edit_dota_search_goal(self, message):
        user_id = message.from_user.id
        if not self.is_user_banned(user_id):
            if message.text in self.search_goals:
                new_search_goal = message.text
                cur = self.con.cursor()
                cur.execute("UPDATE Games SET search_goal=? WHERE id=? AND game=?",
                            (new_search_goal, user_id, "dota 2",))
                self.con.commit()
                cur.close()
                self.bot.send_message(user_id, "Профиль успешно обновлен.", reply_markup=types.ReplyKeyboardRemove())
            else:
                return self.edit_dota_rank(message)

    def delete_profile(self, message, game):
        user_id = message.from_user.id
        if not self.is_user_banned(user_id):
            cur = self.con.cursor()
            cur.execute("DELETE FROM Games WHERE id=? AND game=?", (user_id, game,))
            cur.execute("DELETE FROM Matches WHERE user_id=? AND game=?", (user_id, game,))
            self.con.commit()
            cur.close()
            self.bot.send_message(user_id, "Профиль успешно удален.", reply_markup=types.ReplyKeyboardRemove())

    def get_rank_keyboard(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for rank in self.ranks:
            markup.add(types.KeyboardButton(rank))
        markup.add(types.KeyboardButton("Вернуться"))
        return markup

    def get_rank_dota(self, message, user_profile):
        user_id = message.from_user.id
        if not self.is_user_banned(user_id):
            log_action(message.from_user.id, "get_rank executed")
            if message.text == "Вернуться":
                self.returned(message)
                return
            if message.text in self.ranks:
                user_profile['rank'] = message.text
                self.bot.send_message(user_id, "Выберите цель поиска:", reply_markup=self.get_search_goal_keyboard())
                self.bot.register_next_step_handler(message, self.get_search_goal, user_profile)
            else:
                self.bot.send_message(user_id, "Кажется, такого варианта нет...")
                log_action(message.from_user.id, "rank isnt defined")
                self.bot.send_message(user_id, "Кажется, такого варианта нет...")
                self.bot.register_next_step_handler(message, self.get_rank_dota, user_profile)

    def get_search_goal_keyboard(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for goal in self.search_goals:
            markup.add(types.KeyboardButton(goal))
        return markup

    def get_search_goal(self, message, user_profile):
        user_id = message.from_user.id
        if not self.is_user_banned(user_id):
            if message.text == "Вернуться":
                self.returned(message)
                return
            if message.text in self.search_goals:
                user_profile['search_goal'] = message.text
                self.bot.send_message(user_id, "Анкета создана! Теперь вы можете начать поиск напарников.",
                                      reply_markup=types.ReplyKeyboardRemove())
                cur = self.con.cursor()
                try:
                    sqlite_insert_query = """INSERT INTO Games
                                              (game, id, desc, tg_profile, rank, search_goal)
                                              VALUES
                                              (?, ?, ?, ?, ?, ?);"""
                    column_values = (tuple(user_profile.values()))
                    cur.execute(sqlite_insert_query, column_values)
                    self.con.commit()
                except Exception:
                    self.con.rollback()
                cur.close()
                self.show_random_profile(message, user_profile["game"], user_profile["search_goal"],
                                         user_profile["rank"])
            else:
                self.bot.send_message(user_id, "Кажется, такого варианта нет...")
                self.bot.register_next_step_handler(message, self.get_search_goal, user_profile)

    def get_random_profile_dota(self, user_id, search_goal, rank):
        cursor = self.con.cursor()
        search_goal = search_goal.split("-")
        ranks = {
            "Рекрут": ["Неважно", "Рекрут-Страж"],
            "Страж": ["Неважно", "Рекрут-Страж", "Страж-Рыцарь"],
            "Рыцарь": ["Неважно", "Страж-Рыцарь", "Рыцарь-Герой"],
            "Герой": ["Неважно", "Рыцарь-Герой", "Герой-Легенда"],
            "Легенда": ["Неважно", "Герой-Легенда", "Легенда-Властелин"],
            "Властелин": ["Неважно", "Легенда-Властелин", "Властелин-Божество"],
            "Божество": ["Неважно", "Властелин-Божество", "Божество-Титан"],
            "Титан": ["Неважно", "Божество-Титан", "Титан"],
            "Нет": ["Неважно"]
        }
        cur_rank = ranks[rank]

        # Проверка наличия "Неважно" в целевых рангах текущего пользователя и другого пользователя
        if "Неважно" in cur_rank and "Неважно" in search_goal:
            cursor.execute(
                f"SELECT * FROM Games WHERE game = ? AND id != ? ORDER BY RANDOM() LIMIT 1",
                ("dota 2", user_id))
        elif "Неважно" in cur_rank:
            cursor.execute(
                f"SELECT * FROM Games WHERE game = ? AND id != ? AND rank IN "
                f"({', '.join(['?'] * len(search_goal))}) ORDER BY RANDOM() LIMIT 1",
                ("dota 2", user_id, *search_goal))
        elif "Неважно" in search_goal:
            cursor.execute(
                f"SELECT * FROM Games WHERE game = ? AND id != ? AND search_goal IN "
                f"({', '.join(['?'] * len(cur_rank))}) ORDER BY RANDOM() LIMIT 1",
                ("dota 2", user_id, *cur_rank))
        else:
            cursor.execute(
                f"SELECT * FROM Games WHERE game = ? AND id != ? AND rank IN "
                f"({', '.join(['?'] * len(search_goal))}) AND search_goal IN "
                f"({', '.join(['?'] * len(cur_rank))}) ORDER BY RANDOM() LIMIT 1",
                ("dota 2", user_id, *search_goal, *cur_rank))

        res = cursor.fetchone()
        cursor.close()
        return res

    def get_random_profile(self, user_id, game):
        cursor = self.con.cursor()
        cursor.execute(
            f"SELECT * FROM Games WHERE game = ? AND id != ? ORDER BY RANDOM() LIMIT 1",
            (game, user_id,))
        res = cursor.fetchone()
        cursor.close()
        return res

    def show_random_profile(self, message, game, search_goal, rank):
        user_id = message.chat.id
        if not self.is_user_banned(user_id):
            if game == "dota 2":
                random_profile = self.get_random_profile_dota(user_id, search_goal, rank)
            else:
                random_profile = self.get_random_profile(user_id, game)
            if random_profile:
                self.send_profile(message.chat.id, random_profile, game)
            else:
                self.bot.send_message(user_id, "Извините, но для Вас больше нет анкет.")

    def send_profile(self, chat_id, profile, game):
        user_id = profile[1]
        if not self.is_user_banned(user_id):
            description = profile[2]
            rank = None
            try:
                rank = profile[4]
            except Exception:
                pass
            game = game
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            like_button = types.InlineKeyboardButton(text="Лайк", callback_data=f"like_{user_id}_{game}")
            dislike_button = types.InlineKeyboardButton(text="Пропустить", callback_data=f"dislike_{user_id}_{game}")
            report_button = types.InlineKeyboardButton(text="Report", callback_data=f"report_{user_id}_{game}")
            keyboard.add(like_button, dislike_button, report_button)
            if rank:
                message_text = f"**Описание:** {description}\n**Ранг:** {rank}"
            else:
                message_text = f"**Описание:** {description}\n**Игра:** {game.capitalize()}"
            self.bot.send_message(chat_id, message_text, reply_markup=keyboard, parse_mode='Markdown')

    def get_profile_by_id(self, profile_id, game):
        cursor = self.con.cursor()
        cursor.execute('SELECT * FROM Games WHERE game=? AND id=? LIMIT 1', (game, profile_id,))
        return cursor.fetchone()

    def send_matched_profiles(self, user_id, liked_profile):
        liked_user_id = liked_profile[1]
        game = liked_profile[0]
        cursor = self.con.cursor()
        cursor.execute('SELECT * FROM Games WHERE id=? AND game=? LIMIT 1', (user_id, liked_profile[0]))
        user = cursor.fetchone()
        mutual_like_query = ('SELECT * FROM Matches WHERE '
                             '((user_id=? AND liked_user_id=? AND game=?) OR '
                             '(user_id=? AND liked_user_id=? AND game=?)) LIMIT 1')
        cursor.execute(mutual_like_query, (user_id, liked_user_id, game, liked_user_id, user_id, game))
        mutual_like = cursor.fetchone()
        if mutual_like:
            self.bot.send_message(user_id, f'Ура! Вы взаимно лайкнулись с пользователем '
                                           f'@{self.bot.get_chat(liked_user_id).username}\n'
                                           f'Игра: {liked_profile[0].capitalize()}\nОписание: {liked_profile[2]}!')
            self.bot.send_message(liked_user_id, f'Ура! Вы взаимно лайкнулись с пользователем '
                                                 f'@{self.bot.get_chat(user_id).username}!\n'
                                                 f'Игра: {user[0].capitalize()}\nОписание: {user[2]}!')
            cursor.execute("DELETE FROM Matches WHERE user_id=? or liked_user_id=?", (user_id, user_id,))
            self.con.commit()
        else:
            self.bot.send_message(user_id, f'Вы лайкнули пользователя! '
                                           'Если он вас тоже лайкнет, вы получите уведомление!')
            cursor.execute('INSERT INTO Matches (user_id, liked_user_id, game) VALUES (?, ?, ?)',
                           (user_id, liked_user_id, game,))
            self.con.commit()
            # Уведомим пользователя, которого лайкнули
            self.bot.send_message(liked_user_id, f'Кто-то лайкнул Вас'
                                                 f'\nХотите посмотреть его анкету?',
                                  reply_markup=get_view_profile_keyboard(user_id, game))
        cursor.close()

    def ask_report_reason(self, user_id, reported_profile_id):
        msg = self.bot.send_message(user_id, "Выберите причину жалобы.\nПомините, "
                                             "что за некорректную жалобу Вас могут заблокировать.", reply_markup=None)
        self.bot.register_next_step_handler(msg, self.send_report_reason, user_id, reported_profile_id)

    def send_report_reason(self, message, user_id, reported_profile_id):
        try:
            for i in self.admins:
                self.bot.send_message(i, f"Пользователь {user_id} написал жалобу на {reported_profile_id}, текст:\n\n"
                                         f"{message.text}")
            self.bot.send_message(user_id, f"Жалоба отправлена!")
        except Exception as e:
            self.bot.send_message(user_id, f"Произошла ошибка... Отправьте лог администратору бота @mikufagoff\n{e}")

    def not_accept(self, message):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Принять правила", callback_data="accept_rules"))
        self.bot.send_message(message.chat.id, "Для использования бота необходимо принять правила. "
                                               "https://telegra.ph/Pravila-TeamFiend-03-19",
                              reply_markup=markup)

    def returned(self, message):
        self.bot.send_message(message.chat.id, "Принято.", reply_markup=types.ReplyKeyboardRemove())


if __name__ == "__main__":
    bot_token = ""
    game_finder_bot = GameFinderBot(bot_token)
    game_finder_bot.run()
