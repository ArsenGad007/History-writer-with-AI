# Импортируем библиотеку telebot
import telebot
from telebot import types
from telebot.types import ReplyKeyboardMarkup

# Импортируем функцию gpt для работы с нейросетью
from gpt import answer_gpt, count_tokens
from database import DataBase
from config import API_TOKEN, COUNT_SESSION, TOKENS_IN_SESSION, FOLDER_ID, IAM_TOKEN

import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="log_file.txt",
    filemode="a",
)

logging.info("Запуск Бота")

# Создаём бота
bot = telebot.TeleBot(API_TOKEN)

# Ссылка на бота @AI_Mistral_GPT_Bot

# Создаём объект класса DataBase
db = DataBase('histories.db')

db.create_table('Users')


# Создаёт клавиатуру с указанными кнопками
def menu_keyboard(options):
    buttons = (types.KeyboardButton(text=option) for option in options)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True,
                                   one_time_keyboard=True,
                                   is_persistent=True,
                                   row_width=2,
                                   input_field_placeholder="Тык кнопочку")
    keyboard.add(*buttons)
    return keyboard


@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Проверка на приём сообщения от нейросети
    if db.select_data(user_id, 'handler_enabled', 'Users') != 0:
        # Инициализируем пользователя в базе данных
        db.delete_data(user_id, 'Users')
        db.insert_data(user_id, 'Users')
        db.update_data(user_id, 'answers', " ", 'Users')
        db.update_data(user_id, 'debug_mode', 0, 'Users')
        db.update_data(user_id, 'handler_enabled', 1, 'Users')

    if not isinstance(db.select_data(user_id, 'session', 'Users'), int):
        db.update_data(user_id, 'session', COUNT_SESSION, 'Users')
    if not isinstance(db.select_data(user_id, 'tokens', 'Users'), int):
        db.update_data(user_id, 'session', TOKENS_IN_SESSION, 'Users')

    keyboard = ["/new_story", "/debug", "/debug_mode"]

    bot.send_message(user_id, text=f"Привет, {user_name}! Я бот, который создаёт истории с помощью нейросети. Мы "
                                   f"будем писать историю поочерёдно. Я начну, а ты продолжить. Напиши /new_story, "
                                   f"чтобы начать новую историю. А когда ты закончишь, напиши /end.",
                     reply_markup=menu_keyboard(keyboard))

    logging.info(f"{user_name}: Отправка приветственного сообщения")


@bot.message_handler(func=lambda message:
                     db.select_data(message.from_user.id, 'handler_enabled', 'Users') == 1,
                     commands=['new_story'])
def new_story(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    if db.select_data(user_id, 'session', 'Users') <= 0:
        return "У вас закончились сессии :("
    elif count_tokens(db.select_data(user_id, 'answers', 'Users'), FOLDER_ID, IAM_TOKEN) > TOKENS_IN_SESSION:
        logging.error(f"{user_name}: Закончились токены на сессию")
        return "У вас закончились токены на сессию. Начните новую сессию /new_session"

    keyboard = ["комедия", "фантастика", "хоррор"]
    bot.send_message(user_id, text="Для начала выбери жанр своей истории:", reply_markup=menu_keyboard(keyboard))

    logging.info(f"{user_name}: Отправка сообщения с помощью")
    bot.register_next_step_handler(message, genre)


def genre(message):
    user_id = message.from_user.id

    # Проверка, что сообщение-это не команда
    check = ["комедия", "фантастика", "хоррор"]
    if message.text not in check:
        bot.send_message(user_id, text="Отправь жанр своей истории: комедия, фантастика, хоррор",
                         reply_markup=menu_keyboard(check))
        # Регистрируем следующий шаг на эту же функцию
        bot.register_next_step_handler(message, main_character)
        return

    if message.text == "комедия":
        db.update_data(user_id, 'genre', 'комедия', 'Users')
    elif message.text == "фантастика":
        db.update_data(user_id, 'genre', 'фантастика', 'Users')
    else:
        db.update_data(user_id, 'genre', 'хоррор', 'Users')

    keyboard = ["винни пух", "пятачок", "гарри поттер", "гермиона"]
    bot.send_message(user_id, text="Выбери главного героя:", reply_markup=menu_keyboard(keyboard))
    bot.register_next_step_handler(message, main_character)


def main_character(message):
    user_id = message.from_user.id

    # Проверка, что сообщение-это не команда
    check = ["винни пух", "пятачок", "гарри поттер", "гермиона"]
    if message.text not in check:
        bot.send_message(user_id, text="Отправь героя своей истории: винни пух, пятачок, гарри поттер, гермиона",
                         reply_markup=menu_keyboard(check))
        # Регистрируем следующий шаг на эту же функцию
        bot.register_next_step_handler(message, main_character)
        return

    if message.text == "винни пух":
        db.update_data(user_id, 'character', 'винни пух', 'Users')
    elif message.text == "пятачок":
        db.update_data(user_id, 'character', 'пятачок', 'Users')
    elif message.text == "гарри поттер":
        db.update_data(user_id, 'character', 'гарри поттер', 'Users')
    else:
        db.update_data(user_id, 'character', 'гермиона', 'Users')

    keyboard = ["город", "природа", "остров"]
    bot.send_message(user_id, text="Выбери локацию:\n1)Город: История происходит в современном городе с высокими "
                                   "небоскребами, оживленными улицамии разнообразными районами.\n2)Природа: История "
                                   "происходит в лесу, где растут большие деревья и много разных животных\n3)Остров: "
                                   "История развивается на необитаемом острове сокровищ.",
                     reply_markup=menu_keyboard(keyboard))
    bot.register_next_step_handler(message, location)


def location(message):
    user_id = message.from_user.id

    check = ["город", "природа", "остров"]
    if message.text not in check:
        bot.send_message(user_id, text="Отправь локацию своей истории: город, природа, остров",
                         reply_markup=menu_keyboard(check))
        # Регистрируем следующий шаг на эту же функцию
        bot.register_next_step_handler(message, location)
        return

    if message.text == "город":
        db.update_data(user_id, 'location', 'город', 'Users')
    elif message.text == "природа":
        db.update_data(user_id, 'location', 'природа', 'Users')
    else:
        db.update_data(user_id, 'location', 'остров', 'Users')
    keyboard = ["/begin"]
    bot.send_message(user_id, text="Если ты хочешь, чтобы мы учли ещё какую-то информацию, напиши её сейчас. Или ты "
                                   "можешь сразу переходить к истории написав /begin.",
                     reply_markup=menu_keyboard(keyboard))
    bot.register_next_step_handler(message, choice)


def choice(message):
    user_id = message.from_user.id
    if message.text == "/begin":
        begin(message)
    elif message.content_type == "text":
        db.update_data(user_id, 'info', message.text, 'Users')
        bot.send_message(user_id, text="Спасибо! Всё учтём :)\nНапиши /begin, чтобы начать писать историю.")
        # Регистрируем следующий шаг на эту же функцию
        bot.register_next_step_handler(message, choice)
        return


# Отправка запроса к GPT
def begin(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Проверка, что сообщение-это текст
    if message.content_type != "text":
        bot.send_message(user_id, text="Отправь промт текстовым сообщением")
        # Регистрируем следующий шаг на эту же функцию
        bot.register_next_step_handler(message, begin)
        return

    command_list = ["/start", "/new_story", "/debug"]
    if message.text in command_list:
        bot.send_message(user_id, text="Отправь промт, а не команду")
        # Регистрируем следующий шаг на эту же функцию
        bot.register_next_step_handler(message, begin)
        return

    # Сохраняем полученное сообщение, которое и будет промтом
    user_promt = message.text

    msg = bot.send_message(message.from_user.id, "Загрузка...")
    logging.info(f"{user_name}: Получен промт '{user_promt}'. Запрос к серверу нейросети")

    if db.select_data(user_id, 'debug_mode', 'Users') == 1:
        bot.send_message(user_id, f"Получен промт '{user_promt}'. Запрос к серверу нейросети",
                         reply_markup=types.ReplyKeyboardRemove())

    db.update_data(user_id, 'handler_enabled', 0, 'Users')
    answer = answer_gpt(user_promt, user_id, user_name, db)
    db.update_data(user_id, 'handler_enabled', 1, 'Users')

    bot.delete_message(message.chat.id, msg.message_id)
    bot.send_message(user_id, answer, reply_markup=menu_keyboard(["continue", "end"]))
    bot.register_next_step_handler(message, continue_answer)


# continue_answer - Продолжает ответ на вопрос
def continue_answer(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    if message.text == "end":
        end(message)
    else:
        command_list = ["/start", "/new_story", "/debug"]
        if message.text in command_list:
            bot.send_message(user_id, text="Отправь промт, а не команду")
            # Регистрируем следующий шаг на эту же функцию
            bot.register_next_step_handler(message, continue_answer)
            return

        msg = bot.send_message(message.from_user.id, "Загрузка...")
        logging.info(f"Получен промт {message.text}. Запрос к серверу нейросети")
        if db.select_data(user_id, 'debug_mode', 'Users') == 1:
            bot.send_message(user_id, f"Получен промт {message.text}. Запрос к серверу нейросети",
                             reply_markup=types.ReplyKeyboardRemove())

        db.update_data(user_id, 'handler_enabled', 0, 'Users')
        answer = answer_gpt("Продолжить", user_id, user_name, db)
        db.update_data(user_id, 'handler_enabled', 1, 'Users')

        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_message(user_id, answer, reply_markup=menu_keyboard(["continue", "end"]))
        bot.register_next_step_handler(message, continue_answer)


def end(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    command_list = ["/start", "/new_story", "/debug"]
    if message.text in command_list:
        bot.send_message(user_id, text="Отправь промт, а не команду")
        # Регистрируем следующий шаг на эту же функцию
        bot.register_next_step_handler(message, end)
        return

    msg = bot.send_message(message.from_user.id, "Загрузка...")
    logging.info(f"Получен промт 'end'. Запрос к серверу нейросети")
    if db.select_data(user_id, 'debug_mode', 'Users') == 1:
        bot.send_message(user_id, f"{user_name}: Получен промт 'end'. Запрос к серверу нейросети",
                         reply_markup=types.ReplyKeyboardRemove())

    db.update_data(user_id, 'handler_enabled', 0, 'Users')
    answer = answer_gpt("end", user_id, user_name, db)
    db.update_data(user_id, 'handler_enabled', 1, 'Users')

    bot.delete_message(message.chat.id, msg.message_id)
    bot.send_message(user_id, answer, reply_markup=menu_keyboard(["/new_story", "/debug"]))
    return


# Обработчик команды /debug - Отправляет Log файл
@bot.message_handler(func=lambda message:
                     db.select_data(message.from_user.id, 'handler_enabled', 'Users') == 1,
                     commands=['debug'])
def send_logs(message):
    user_name = message.from_user.first_name

    logging.info(f"{user_name}: Отправка Log файла")

    with open("log_file.txt", "rb") as f:
        bot.send_document(message.chat.id, f)


@bot.message_handler(func=lambda message:
                     db.select_data(message.from_user.id, 'handler_enabled', 'Users') == 1,
                     commands=['new_session'])
def new_session(message):
    user_id = message.from_user.id
    if db.select_data(user_id, 'session', 'Users') <= 0:
        return "У вас закончились сессии :("
    db.update_data(user_id, 'session', db.select_data(user_id, 'session', 'Users')-1,
                   'Users')
    db.update_data(user_id, 'session', TOKENS_IN_SESSION, 'Users')


@bot.message_handler(func=lambda message:
                     db.select_data(message.from_user.id, 'handler_enabled', 'Users') == 1,
                     commands=['debug_mode'])
def debug_mode(message):
    user_id = message.from_user.id
    db.update_data(user_id, 'debug_mode', 1, 'Users')
    bot.send_message(message.from_user.id, "Режим отладки включен")


# Обработчик текстовых сообщений пользователя
@bot.message_handler(func=lambda message:
                     db.select_data(message.from_user.id, 'handler_enabled', 'Users') == 1,
                     content_types=['text'])
def repeat_message(message):
    keyboard = ["/new_story", "/debug", "/debug_mode"]
    bot.send_message(message.from_user.id, "Я не понимаю что вы хотите. Чтобы начать сценарий напишите /new_story ",
                     reply_markup=menu_keyboard(keyboard))


@bot.message_handler(func=lambda message:
                     db.select_data(message.from_user.id, 'handler_enabled', 'Users') == 0)
def wait(message):
    bot.send_message(message.from_user.id, "Подождите ответа от нейросети")


# Запускаем бота
bot.polling()
