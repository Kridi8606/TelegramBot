import sqlite3
import time
import asyncio
import telebot
from telebot import types
import json
from database.db import User_database, Hidden_continuation_database
from datetime import datetime
from pathlib import Path
from tools.markups import Start_markup

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    BOT_TOKEN, ADMINS_ID, SUPPORT_CHAT = config['BOT_TOKEN'], config['ADMINS_ID'], config['SUPPORT_CHAT']

bot = telebot.TeleBot(BOT_TOKEN)
bot.delete_webhook()
db = User_database(str(Path.cwd() / 'database' / 'database.db'))
callback_database = Hidden_continuation_database(str(Path.cwd() / 'database' / 'database.db'))


# Тут работаем с командой start
@bot.message_handler(commands=['start'])
def welcome_start(message):
    try:
        text = message.from_user.first_name + ', приветствую вас!'
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=Start_markup)
    except Exception as ex:
        print('Ops... Hello error')
        print(ex)


@bot.message_handler(content_types=['text'], func=lambda message: str(message.chat.id) != SUPPORT_CHAT and SUPPORT_CHAT != 'None')
def forwarding_to_support_chat(message):
    button = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton('Скрыть', callback_data='unseen')
    button.add(btn)
    bot.forward_message(SUPPORT_CHAT, message.chat.id, message.message_id)
    text = 'Ваш вопрос отправлен в чат поддержки, вскоре вы получите на него ответ.'
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=button)
    print(message)


@bot.message_handler(content_types=['text'], func=lambda message: str(message.chat.id) == SUPPORT_CHAT and SUPPORT_CHAT != 'None' and message.reply_to_message is not None)
def answer(message):
    text = '> ' + message.reply_to_message.text + '\n\n' + message.text
    bot.send_message(message.reply_to_message.forward_from.id, text, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.data == 'start_markup_support_chat':
            buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            btn1 = types.KeyboardButton('Да')
            btn2 = types.KeyboardButton('Нет')
            buttons.add(btn1, btn2)
            text = 'Хотите изменить чат поддержки?'
            message = bot.send_message(call.from_user.id, text, parse_mode='Markdown', reply_markup=buttons)
            bot.register_next_step_handler(message, approve_change_support_chat_id)
        elif call.data == 'unseen':
            bot.delete_message(call.message.chat.id, call.message.id)
        elif callback_database.check_button(int(call.data)):
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

def approve_change_support_chat_id(message):
    if message.text.lower() == 'да':
        text = 'Хорошо, отправьте id чата, который хотите использовать.'
        bot.send_message(message.from_user.id, text, parse_mode='Markdown')
        bot.register_next_step_handler(message, change_support_chat_id)
    elif message.text.lower() == 'нет':
        text = 'Хорошо, отмена.'
        bot.send_message(message.from_user.id, text, parse_mode='Markdown')
    else:
        text = 'Этот ответ не был ожидаем, так что отмена.'
        bot.send_message(message.from_user.id, text, parse_mode='Markdown')


def change_support_chat_id(message):
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    config['SUPPORT_CHAT'] = message.text
    global SUPPORT_CHAT
    SUPPORT_CHAT = message.text
    with open('config.json', 'w') as f:
        f.write(json.dumps(config))
    text = 'Id чата поддержки изменено на ' + message.text
    bot.send_message(message.from_user.id, text, parse_mode='Markdown', disable_web_page_preview=True)


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
    if message.from_user.id in ADMINS_ID:
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
            list_of_users = db.get_users()
            for user in list_of_users:
                bot.send_message(user[0], mail_text)
                # у телеграмма вроде есть ограничение 30 сообщ/сек, так что на всякий случай добавила задержку
                time.sleep(0.1)
            bot.send_message(message.chat.id, text='Успех!', reply_markup=removing_buttons)
        except sqlite3.Error:
            print('Упс! Проблемы с соединением с базой данных')
            bot.send_message(message.chat.id, 'Упс! Проблемы с соединением с базой данных',
                             reply_markup=removing_buttons)
        except Exception:
            print('Кажется, что-то пошло не так...')
            bot.send_message(message.chat.id, 'Кажется, что-то пошло не так...', reply_markup=removing_buttons)
    elif message.text == 'Отмена':
        bot.send_message(message.chat.id, text='Вы отменили рассылку', reply_markup=removing_buttons)
    else:
        bot.send_message(message.chat.id, 'Ну вот, теперь начинайте заново', reply_markup=removing_buttons)


async def checking_subscription():
    current_date_time = datetime.now()
    current_time = current_date_time.time()
    sleep_time = (24 - current_time.hour, 60 - current_time.minute, 60 - current_time.second + 5)
    await asyncio.sleep(sleep_time[0] * 60 * 60 + sleep_time[1] * 60 + sleep_time[2])
    while RUNNING:
        current_date_time = datetime.now().timestamp()
        all_users = db.get_all()
        for i in all_users:
            if i[3]:
                if current_date_time > i[2] - 300:  # конец подписки
                    db.upd_user_status(i[1], 0)
                    with open(Path.cwd() / 'messages' / 'end_subscription_message.txt', 'r', encoding='utf-8') as f:
                        bot.send_message(GROUP_ID, f.read(), parse_mode='Markdown',
                                         disable_web_page_preview=True)
                elif 604500 < i[2] - current_date_time < 605100:  # предупреждение за неделю
                    with open(Path.cwd() / 'messages' / 'week_until_end_subscription_message.txt', 'r',
                              encoding='utf-8') as f:
                        bot.send_message(GROUP_ID, f.read(), parse_mode='Markdown',
                                         disable_web_page_preview=True)
                elif 258900 < i[2] - current_date_time < 259500:  # предупреждение за три дня
                    with open(Path.cwd() / 'messages' / 'three_days_until_end_subscription.txt', 'r',
                              encoding='utf-8') as f:
                        bot.send_message(GROUP_ID, f.read(), parse_mode='Markdown',
                                         disable_web_page_preview=True)
                elif 86100 < i[2] - current_date_time < 86700:  # предупреждение за один день
                    with open(Path.cwd() / 'messages' / 'day_until_end_subscription.txt', 'r', encoding='utf-8') as f:
                        bot.send_message(GROUP_ID, f.read(), parse_mode='Markdown',
                                         disable_web_page_preview=True)
        await asyncio.sleep(24 * 60 * 60)  # время в секундах
    print('Конец')


if __name__ == "__main__":
    print("Бот запущен")
    bot.polling()
print('Бот остановлен')
