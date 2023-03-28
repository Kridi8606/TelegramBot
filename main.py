import sqlite3
import time

import telebot
from telebot import types
from config import BOT_TOKEN, DATABASE_FILE
from database.db import User_database

bot = telebot.TeleBot(BOT_TOKEN)
db = User_database(DATABASE_FILE)


# Тут работаем с командой start
@bot.message_handler(commands=['start'])
def welcome_start(message):
    bot.send_message(message.chat.id, 'Приветствую тебя user')


# Тут работаем с командой help
@bot.message_handler(commands=['help'])
def welcome_help(message):
    bot.send_message(message.chat.id, 'Чем я могу тебе помочь?')


@bot.chat_join_request_handler()
def invite(message):
    bot.approve_chat_join_request(message.chat.id, message.from_user.id)
    bot.send_message(message.from_user.id, 'Приветственный текст')


# рассылка
@bot.message_handler(commands=['startmailing'])
def start_mailing(message):
    # здесь (возможно) будет проверка, админ ли пользователь, написавший команду
    text = bot.send_message(message.chat.id, 'Пришлите текст рассылки')
    bot.register_next_step_handler(text, approve_mailing)


def approve_mailing(message):
    mail_text = message.text
    bot.send_message(message.chat.id, f'Текст вашей рассылки - {mail_text}')
    buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton('Подтвердить')
    btn2 = types.KeyboardButton('Отмена')
    buttons.add(btn1, btn2)
    bot.send_message(message.chat.id, text='Разослать? (Это может занять некоторое время)', reply_markup=buttons)
    bot.register_next_step_handler(message, sendall, mail_text)


def sendall(message, mail_text):
    removing_buttons = types.ReplyKeyboardRemove()
    if message.text == 'Подтвердить':
        try:
            list_of_users = db.get_all_users()
            for user in list_of_users:
                bot.send_message(user[0], mail_text)
                # у телеграмма вроде есть ограничение 30 сообщ/сек, так что на всякий случай добавила задержку
                time.sleep(0.1)
            bot.send_message(message.chat.id, text='Успех!', reply_markup=removing_buttons)
        except sqlite3.Error:
                print('Упс! Проблемы с соединением с базой данных')
                bot.send_message(message.chat.id, 'Упс! Проблемы с соединением с базой данных', reply_markup=removing_buttons)
        except Exception:
            print('Кажется, что-то пошло не так...')
            bot.send_message(message.chat.id, 'Кажется, что-то пошло не так...', reply_markup=removing_buttons)
    elif message.text == 'Отмена':
        bot.send_message(message.chat.id, text='Вы отменили рассылку', reply_markup=removing_buttons)
    else:
        bot.send_message(message.chat.id, 'Ну вот, теперь начинайте заново', reply_markup=removing_buttons)


# @bot.message.hamdler()
# def leave(message):
#     print(message)


if __name__ == "__main__":
    print("Бот запущен")
    bot.polling()
print('Бот остановлен')
