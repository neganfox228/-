import telebot
from telebot import types
import psycopg2
import datetime

conn = psycopg2.connect(user="postgres",
                        password="0000",
                        host="127.0.0.1",
                        port="5432",
                        database="stol")
cur = conn.cursor()
bot = telebot.TeleBot("6525136024:AAFpVOa0ClnokyDW5DKR8W9LgMYbMQ1gkaQ")
user_states = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id

    cur.execute("SELECT status FROM users WHERE username = %s", (str(user_id),))
    user_status = cur.fetchone()

    if user_status and user_status[0] == 'активный':
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=create_main_menu_keyboard())
    elif user_status and user_status[0] == 'ожидание':
        bot.send_message(message.chat.id, "Ваша заявка на рассмотрении. Пожалуйста, подождите.")
    else:
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button = types.KeyboardButton("Авторизоваться")
        keyboard.add(button)
        msg = bot.reply_to(message, "Добро пожаловать! Нажмите кнопку 'Авторизоваться' для начала:", reply_markup=keyboard)
        bot.register_next_step_handler(msg, ask_full_name)

def ask_full_name(message):
    if message.text == 'Авторизоваться':
        user_id = message.from_user.id
        user_states[user_id] = {}
        msg = bot.reply_to(message, "Введите ваше ФИО:")
        bot.register_next_step_handler(msg, ask_departure_date)
    else:
        bot.reply_to(message, "Пожалуйста, воспользуйтесь кнопкой 'Авторизоваться'.")

def ask_departure_date(message):
    full_name = message.text
    user_id = message.from_user.id
    user_states[user_id]['full_name'] = full_name
    msg = bot.reply_to(message, "Введите дату выезда в формате ДД.ММ.ГГГГ (например, 01.01.2024):")
    bot.register_next_step_handler(msg, process_departure_date)

def process_departure_date(message):
    date_text = message.text
    user_id = message.from_user.id

    try:
        departure_date = datetime.datetime.strptime(date_text, '%d.%m.%Y')
        current_year = datetime.datetime.now().year
        if departure_date.year != current_year or departure_date.year < 2024:
            bot.send_message(message.chat.id, "Некорректный год.")
            ask_departure_date(message)
        else:
            full_name = user_states[user_id]['full_name']
            user_id = save_user_info(full_name, departure_date, user_id)
            bot.send_message(message.chat.id, "Ваша заявка отправлена на рассмотрение.")

            bot.send_message(message.chat.id, "Ваша заявка одобрена! Выберите действие:", reply_markup=create_main_menu_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "Некорректный формат даты.")
        ask_departure_date(message)


def save_user_info(full_name, departure_date, user_id):
    sql = "INSERT INTO users (full_name, departure_date, status, username) VALUES (%s, %s, 'ожидание', %s) RETURNING user_id"
    cur.execute(sql, (full_name, departure_date, user_id))
    user_id = cur.fetchone()[0]
    conn.commit()
    return user_id

def create_main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Меню"))
    keyboard.add(types.KeyboardButton("Заказать"))
    keyboard.add(types.KeyboardButton("Отменить заказ"))
    return keyboard

# Запуск бота
bot.polling()