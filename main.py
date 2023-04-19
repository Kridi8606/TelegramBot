import sqlite3
import time
import asyncio
import telebot
from telebot import types
import json
import threading
import schedule
from database.db import User_database, Hidden_continuation_database, Banned_users
from datetime import datetime
from pathlib import Path
from tools.markups import Start_markup
from tools.ban_message_parser import ban_message_parser

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    BOT_TOKEN, ADMINS_ID, SUPPORT_CHAT, LIST_ID = config['BOT_TOKEN'], config['ADMINS_ID'], config['SUPPORT_CHAT'], config['LIST_ID']

bot = telebot.TeleBot(BOT_TOKEN)
bot.delete_webhook()
db = User_database(str(Path.cwd() / 'database' / 'database.db'))
callback_database = Hidden_continuation_database(str(Path.cwd() / 'database' / 'database.db'))
bans_database = Banned_users(str(Path.cwd() / 'database' / 'database.db'))


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
    if not bans_database.check_user(message.from_user.id):
        button = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Скрыть', callback_data='unseen')
        button.add(btn)
        bot.forward_message(SUPPORT_CHAT, message.chat.id, message.message_id)
        text = 'Ваш вопрос отправлен в чат поддержки, вскоре вы получите на него ответ.'
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=button)
    else:
        button = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Скрыть', callback_data='unseen')
        button.add(btn)
        info = bans_database.get_user_info(message.from_user.id)
        text = 'Ваш вопрос не был отправлен в чат поддержки. Вам запрещено отправлять сообщения в чат поддержки до ' + datetime.fromtimestamp(info[0]).date().isoformat()
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=button)


@bot.message_handler(commands=['ban'], func=lambda message: str(message.chat.id) == SUPPORT_CHAT and SUPPORT_CHAT != 'None' and message.reply_to_message is not None)
def ban(message):
    try:
        res = ban_message_parser(message.text)
        if bans_database.check_user(message.reply_to_message.forward_from.id):
            bans_database.upd_user_time(message.reply_to_message.forward_from.id, res['time'])
            text = 'Длительность вашей блокировки изменена.\nНовое количество дней блокировки начиная с этого момента — ' + res['days']
            bot.send_message(message.reply_to_message.forward_from.id, text, parse_mode='Markdown')
        else:
            bans_database.add_user(message.reply_to_message.forward_from.id, message.reply_to_message.forward_from.username, res['time'], res['reason'])
            text = 'Ваша возможность писать в поддержку ограничена.\nКоличество дней блокировки начиная с этого момента — ' + \
                   res['days'] + '.\nПричина: ' + str(res['reason'])
            bot.send_message(message.reply_to_message.forward_from.id, text, parse_mode='Markdown')
        text = 'Ограничения произведены успешно.'
        bot.reply_to(message, text)
    except Exception as ex:
        text = 'Произошла ошибка!\n' + str(ex) + '\nПрошу вас, используйте теги примерно так:\n[REASON::<причина бана>]\n[TIME::<количество дней бана>]'
        bot.reply_to(message, text)
        print(str(ex))


@bot.message_handler(commands=['cancel_ban'], func=lambda message: str(message.chat.id) == SUPPORT_CHAT and SUPPORT_CHAT != 'None' and message.reply_to_message is not None)
def cancel_ban(message):
    try:
        if bans_database.check_user(message.reply_to_message.forward_from.id):
            bans_database.delete_user(message.reply_to_message.forward_from.id)
            text = 'С пользователя успешно сняты ограничения.'
            bot.reply_to(message, text)
            text = "С вас сняты ограничения."
            bot.send_message(message.reply_to_message.forward_from.id, text, parse_mode='Markdown')
        else:
            text = 'Данный пользователь не находится под ограничениями на данный момент.'
            bot.reply_to(message, text)
    except Exception as ex:
        text = 'Произошла ошибка!\n' + str(ex)
        bot.reply_to(message, text)
        print(str(ex))


@bot.message_handler(commands=['cancel_ban'], func=lambda message: str(message.chat.id) == SUPPORT_CHAT and SUPPORT_CHAT != 'None' and message.reply_to_message is None)
def cancel_ban_id(message):
    try:
        user_id = int(message.text.split()[-1])
    except:
        text = 'Id указано некорректно.'
        bot.reply_to(message, text)
        return
    try:
        if bans_database.check_user(user_id):
            bans_database.delete_user(user_id)
            text = 'С пользователя успешно сняты ограничения.'
            bot.reply_to(message, text)
            text = "С вас сняты ограничения."
            bot.send_message(user_id, text, parse_mode='Markdown')
        else:
            text = 'Данный пользователь не находится под ограничениями на данный момент.'
            bot.reply_to(message, text)
    except Exception as ex:
        text = 'Произошла ошибка!\n' + str(ex)
        bot.reply_to(message, text)
        print(str(ex))


@bot.message_handler(commands=['ban_info'], func=lambda message: str(message.chat.id) == SUPPORT_CHAT and SUPPORT_CHAT != 'None')
def user_info(message):
    try:
        user_id = int(message.text.split()[-1])
    except:
        text = 'Id указано некорректно.'
        bot.reply_to(message, text)
        return
    try:
        if bans_database.check_user(user_id):
            info = bans_database.get_user_info(user_id)
            text = 'До ' + datetime.fromtimestamp(info[0]).date().isoformat() + '\nПричина: ' + info[1]
            bot.reply_to(message, text)
        else:
            text = 'Данный пользователь не находится под ограничениями на данный момент.'
            bot.reply_to(message, text)
    except Exception as ex:
        text = 'Произошла ошибка!\n' + str(ex)
        bot.reply_to(message, text)
        print(str(ex))


@bot.message_handler(commands=['ban_list'], func=lambda message: str(message.chat.id) == SUPPORT_CHAT and SUPPORT_CHAT != 'None')
def ban_list(message):
    lst = bans_database.get_users()
    text = 'Список забаненных:\n'
    for i in lst:
        text += '@' + i[0] + ': ' + str(i[1]) + '\n'
    bot.reply_to(message, text)

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
            if not db.check_user(message.from_user.id):
                db.add_user(message.from_user.id, datetime.now().timestamp(), 0)
            if db.check_user_status(message.from_user.id):
                bot.approve_chat_join_request(message.chat.id, message.from_user.id)
                with open(Path.cwd() / 'messages' / 'welcome_message.txt', 'r', encoding='utf-8') as f:
                    bot.send_message(message.from_user.id, f.read(), parse_mode='Markdown', disable_web_page_preview=True)
            else:
                bot.decline_chat_join_request(message.chat.id, message.from_user.id)
                with open(Path.cwd() / 'messages' / 'no_welcome_message.txt', 'r', encoding='utf-8') as f:
                    bot.send_message(message.from_user.id, f.read(), parse_mode='Markdown', disable_web_page_preview=True)
        else:
            with open(Path.cwd() / 'messages' / 'already_member.txt', 'r', encoding='utf-8') as f:
                bot.send_message(message.from_user.id, f.read(), parse_mode='Markdown', disable_web_page_preview=True)
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


def checking_subscription():
    current_date_time = datetime.now().timestamp()
    all_users = db.get_all()
    for i in all_users:
        if i[3]:
            if current_date_time > i[2] - 300:  # конец подписки
                try:
                    normal_kick(i[1])
                    db.upd_user_status(i[1], 0)
                except Exception as ex:
                    print("Выгнать человека не удалось\n" + str(ex))
                with open(Path.cwd() / 'messages' / 'end_subscription_message.txt', 'r', encoding='utf-8') as f:
                    bot.send_message(LIST_ID, f.read(), parse_mode='Markdown',
                                     disable_web_page_preview=True)
            elif 604500 < i[2] - current_date_time < 605100:  # предупреждение за неделю
                with open(Path.cwd() / 'messages' / 'week_until_end_subscription_message.txt', 'r',
                          encoding='utf-8') as f:
                    bot.send_message(LIST_ID, f.read(), parse_mode='Markdown',
                                     disable_web_page_preview=True)
            elif 258900 < i[2] - current_date_time < 259500:  # предупреждение за три дня
                with open(Path.cwd() / 'messages' / 'three_days_until_end_subscription.txt', 'r',
                          encoding='utf-8') as f:
                    bot.send_message(LIST_ID, f.read(), parse_mode='Markdown',
                                     disable_web_page_preview=True)
            elif 86100 < i[2] - current_date_time < 86700:  # предупреждение за один день
                with open(Path.cwd() / 'messages' / 'day_until_end_subscription.txt', 'r', encoding='utf-8') as f:
                    bot.send_message(LIST_ID, f.read(), parse_mode='Markdown',
                                     disable_web_page_preview=True)


def check_bans():
    current_date_time = datetime.now().timestamp()
    all_bans = bans_database.get_all_users()
    for i in all_bans:
        if current_date_time > i[3] - 300:
            try:
                bans_database.delete_user(i[1])
            except Exception as ex:
                print("Не удалось удалить строку из таблицы bans")
                print(ex)
                return
            try:
                text = 'С вас сняты ограничения'
                bot.send_message(i[1], text, parse_mode='Markdown')
            except Exception as ex:
                print(ex)


def normal_kick(user_id):
    try:
        bot.kick_chat_member(LIST_ID, user_id)
        bot.unban_chat_member(LIST_ID, user_id)
    except:
        pass



def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()

def time_checker():
    trigger_time = "20:07"
    schedule.every().day.at(trigger_time).do(run_threaded, checking_subscription)
    schedule.every().day.at(trigger_time).do(run_threaded, check_bans)
    while RUNNING:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    thread = threading.Thread(target=time_checker)
    RUNNING = True
    thread.start()
    print("Бот запущен")
    bot.polling()
    RUNNING = False
print('Бот остановлен')
