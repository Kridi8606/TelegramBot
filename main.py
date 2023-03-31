import sqlite3
import time

import telebot
from telebot import types
from config import BOT_TOKEN
from database.db import User_database, Hidden_continuation_database
from datetime import datetime
from pathlib import Path

bot = telebot.TeleBot(BOT_TOKEN)
bot.delete_webhook()
db = User_database(str(Path.cwd() / 'database' / 'database.db'))
callback_database = Hidden_continuation_database(str(Path.cwd() / 'database' / 'database.db'))


# Тут работаем с командой start
@bot.message_handler(commands=['start'])
def welcome_start(message):
    try:
        text = message.from_user.first_name + ', приветствую вас!'
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    except Exception as ex:
        print('Ops... Hello error')
        print(ex)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if callback_database.check_button(int(call.data)):
            callback, sub_event, no_sub_event, condition = callback_database.get_button(int(call.data))
            flag = True
            if condition != 'None':
                for i in condition.split(';'):
                    try:
                        if bot.get_chat_member(i, call.from_user.id).status == 'left':
                            flag = False
                    except:
                        flag = False
                        break
            if flag:
                bot.answer_callback_query(call.id, show_alert=True, text=sub_event)
            else:
                bot.answer_callback_query(call.id, show_alert=True, text=no_sub_event)
    except Exception as ex:
        print('Ops... callback error')
        print(ex)


@bot.chat_join_request_handler()
def invite(message):
    try:
        flag = False
        try:
            if bot.get_chat_member(message.chat.id, message.from_user.id).status == 'left':
                flag = True
        except:
            flag = True
        if flag:
            bot.approve_chat_join_request(message.chat.id, message.from_user.id)
        with open(Path.cwd() / 'messages' / 'welcome_message.txt', 'r', encoding='utf-8') as f:
            bot.send_message(message.from_user.id, f.read(), parse_mode='Markdown', disable_web_page_preview=True)
        if not db.check_user(message.from_user.id):
            db.add_user(message.from_user.id, datetime.now().timestamp(), 1)
    except Exception as ex:
        print('Ops...\n', ex)


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



if __name__ == "__main__":
    print("Бот запущен")
    bot.polling()
print('Бот остановлен')
