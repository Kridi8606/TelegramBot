import sqlite3
import time
import validators
import json
import threading
import schedule
import telebot
from telebot import types
from telebot.storage import StateMemoryStorage
from database.db import User_database, Banned_users
from datetime import datetime
from pathlib import Path
from tools.markups import Start_markup
from tools.ban_message_parser import ban_message_parser
from tools.my_states import MyStates

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    BOT_TOKEN = config['BOT_TOKEN']
    ADMINS_ID = config['ADMINS_ID']
    SUPPORT_CHAT = config['SUPPORT_CHAT']
    LIST_ID = config['LIST_ID']

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(BOT_TOKEN, state_storage=state_storage)
bot.delete_webhook()
db = User_database(str(Path.cwd() / 'database' / 'database.db'))
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


@bot.message_handler(commands=['ban'], func=lambda message: str(
    message.chat.id) == SUPPORT_CHAT and SUPPORT_CHAT != 'None' and message.reply_to_message is not None)
def ban(message):
    try:
        res = ban_message_parser(message.text)
        if bans_database.check_user(message.reply_to_message.forward_from.id):
            bans_database.upd_user_time(message.reply_to_message.forward_from.id, res['time'])
            with open('ban_write_update.txt', 'r', encoding='utf-8') as file:
                text = file.read() + res['days']
            bot.send_message(message.reply_to_message.forward_from.id, text, parse_mode='Markdown')
        else:
            bans_database.add_user(message.reply_to_message.forward_from.id,
                                   message.reply_to_message.forward_from.username, res['time'], res['reason'])
            with open('ban_write.txt', 'r', encoding='utf-8') as file:
                text = file.read() + res['days'] + '.\nПричина: ' + str(res['reason'])
            bot.send_message(message.reply_to_message.forward_from.id, text, parse_mode='Markdown')
        text = 'Ограничения произведены успешно.'
        bot.reply_to(message, text)
    except Exception as ex:
        with open('ban_tags_error.txt', 'r', encoding='utf-8') as file:
            text = 'Произошла ошибка!\n' + str(ex) + file.read()
        bot.reply_to(message, text)
        print(str(ex))


@bot.message_handler(commands=['cancel_ban'], func=lambda message: str(
    message.chat.id) == SUPPORT_CHAT and SUPPORT_CHAT != 'None' and message.reply_to_message is not None)
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


@bot.message_handler(commands=['cancel_ban'], func=lambda message: str(
    message.chat.id) == SUPPORT_CHAT and SUPPORT_CHAT != 'None' and message.reply_to_message is None)
def cancel_ban_id(message):
    try:
        user_id = int(message.text.split()[-1])
    except ValueError:
        text = 'Id указано некорректно.'
        bot.reply_to(message, text)
        return
    except Exception as ex:
        text = 'Произошла ошибка!\n' + str(ex)
        bot.reply_to(message, text)
        print(str(ex))
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


@bot.message_handler(commands=['ban_info'],
                     func=lambda message: str(message.chat.id) == SUPPORT_CHAT and SUPPORT_CHAT != 'None')
def user_info(message):
    try:
        user_id = int(message.text.split()[-1])
    except ValueError:
        text = 'Id указано некорректно.'
        bot.reply_to(message, text)
        return
    except Exception as ex:
        text = 'Произошла ошибка!\n' + str(ex)
        bot.reply_to(message, text)
        print(str(ex))
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


@bot.message_handler(commands=['ban_list'],
                     func=lambda message: str(message.chat.id) == SUPPORT_CHAT and SUPPORT_CHAT != 'None')
def ban_list(message):
    lst = bans_database.get_users()
    text = 'Список забаненных:\n'
    for i in lst:
        text += '@' + i[0] + ': ' + str(i[1]) + '\n'
    bot.reply_to(message, text)


@bot.message_handler(content_types=['text'], func=lambda message: str(
    message.chat.id) == SUPPORT_CHAT and SUPPORT_CHAT != 'None' and message.reply_to_message is not None)
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
    try:
        text = "Теперь это чат поддержки"
        bot.send_message(message.text, text, parse_mode='Markdown', disable_web_page_preview=True)
        with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        config['SUPPORT_CHAT'] = message.text
        global SUPPORT_CHAT
        SUPPORT_CHAT = message.text
        with open('config.json', 'w') as file:
            file.write(json.dumps(config, indent=4))
        text = 'Id чата поддержки изменено на ' + message.text
        bot.send_message(message.from_user.id, text, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as ex:
        text = 'Ошибка. Возможно вы не дали боту возможность писать в чате, который хотите сделать чатом поддержки.'
        text += '\n\n' + str(ex)
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
                with open(Path.cwd() / 'messages' / 'welcome_message.txt', 'r', encoding='utf-8') as file:
                    bot.send_message(message.from_user.id, file.read(), parse_mode='Markdown',
                                     disable_web_page_preview=True)
            else:
                bot.decline_chat_join_request(message.chat.id, message.from_user.id)
                with open(Path.cwd() / 'messages' / 'no_welcome_message.txt', 'r', encoding='utf-8') as file:
                    bot.send_message(message.from_user.id, file.read(), parse_mode='Markdown',
                                     disable_web_page_preview=True)
        else:
            with open(Path.cwd() / 'messages' / 'already_member.txt', 'r', encoding='utf-8') as file:
                bot.send_message(message.from_user.id, file.read(), parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as ex:
        print('Ops...\n', ex)


# рассылка
@bot.message_handler(commands=['startmailing'])
def start_mailing(message):
    if message.from_user.id in ADMINS_ID:
        text = bot.send_message(message.chat.id, 'Пришлите текст рассылки')
        bot.register_next_step_handler(text, approve)
        bot.set_state(message.from_user.id, MyStates.mailing_text, message.chat.id)


@bot.message_handler(state=MyStates.mailing_text)
def approve(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['mailing_text'] = message.text
    bot.send_message(message.chat.id, f'Текст вашей рассылки-{message.text}')
    btns = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Да')
    btn2 = types.KeyboardButton('Нет')
    btn3 = types.KeyboardButton('Отмена')
    btns.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, 'Добавить кнопку с ссылкой?', reply_markup=btns)
    bot.set_state(message.from_user.id, MyStates.adding_button, message.chat.id)


@bot.message_handler(state=MyStates.adding_button)
def answer(message):
    removing_buttons = types.ReplyKeyboardRemove()
    if message.text == 'Да':
        bot.send_message(message.chat.id, 'Отлично, теперь пришлите текст для кнопки', reply_markup=removing_buttons)
        bot.set_state(message.from_user.id, MyStates.button_text, message.chat.id)
    elif message.text == 'Нет':
        bot.send_message(message.chat.id, 'Отлично, переходим к финальной проверке', reply_markup=removing_buttons)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['button_text'] = ''
            data['button_link'] = ''
            final_approve(data, message.chat.id)
        bot.set_state(message.from_user.id, MyStates.final_approve, message.chat.id)
    elif message.text == 'Отмена':
        bot.send_message(message.chat.id, 'Вы отменили рассылку', reply_markup=removing_buttons)
        bot.delete_state(message.from_user.id, message.chat.id)
    else:
        bot.send_message(message.chat.id, 'Пожалуйста, воспользуйтесь кнопками')


@bot.message_handler(state=MyStates.button_text)
def add_button_text(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['button_text'] = message.text
    bot.send_message(message.chat.id, 'Теперь пришлите ссылку для кнопки')
    bot.set_state(message.from_user.id, MyStates.button_link, message.chat.id)


@bot.message_handler(state=MyStates.button_link)
def add_button_link(message):
    if not validators.url(message.text):
        bot.send_message(message.chat.id, 'Это не ссылка')
    else:
        bot.set_state(message.from_user.id, MyStates.final_approve, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['button_link'] = message.text
        final_approve(data, message.chat.id, button=True)


def final_approve(data, chat_id, button=False):
    buttons = None
    if button:
        buttons = types.InlineKeyboardMarkup()
        b = types.InlineKeyboardButton(text=data['button_text'], url=data['button_link'])
        buttons.add(b)
    bot.send_message(chat_id, 'Вот как выглядит ваша рассылка:')
    bot.send_message(chat_id, text=data['mailing_text'], reply_markup=buttons)
    final_confirm_buttons = types.ReplyKeyboardMarkup(resize_keyboard=True)
    confirm_btn = types.KeyboardButton('Да')
    cancel_btn = types.KeyboardButton('Отмена')
    final_confirm_buttons.add(confirm_btn, cancel_btn)
    bot.send_message(chat_id, 'Начать рассылку? (Это может занять некоторое время)', reply_markup=final_confirm_buttons)


@bot.message_handler(state=MyStates.final_approve)
def answer(message):
    removing_btns = types.ReplyKeyboardRemove()
    if message.text == 'Да':
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            mail_text = data['mailing_text']
            btn_text = data['button_text']
            btn_link = data['button_link']
            sendall(message, mail_text, btn_text, btn_link)
    elif message.text == 'Отмена':
        bot.send_message(message.chat.id, 'Вы отменили рассылку', reply_markup=removing_btns)
        bot.delete_state(message.from_user.id, message.chat.id)
    else:
        bot.send_message(message.chat.id, 'Пожалуйста, воспользуйтесь кнопками')


def sendall(message, mail_text, btn_text, btn_link):
    removing_buttons = types.ReplyKeyboardRemove()
    mail_btns = None
    if btn_text and btn_link:
        mail_btns = types.InlineKeyboardMarkup(row_width=1)
        mail_btn = types.InlineKeyboardButton(text=btn_text, url=btn_link)
        mail_btns.add(mail_btn)
    try:
        list_of_users = db.get_all_users()
        for user in list_of_users:
            bot.send_message(user[0], text=mail_text, reply_markup=mail_btns)
            # у телеграмма вроде есть ограничение 30 сообщ/сек, так что на всякий случай добавила задержку
            time.sleep(0.1)
        bot.send_message(message.chat.id, text='Успех!', reply_markup=removing_buttons)
        bot.set_state(message.from_user.id, MyStates.neutral, message.chat.id)
    except sqlite3.Error:
        bot.send_message(message.chat.id, 'Упс! Проблемы с соединением с базой данных',
                         reply_markup=removing_buttons)
    except Exception as ex:
        bot.send_message(message.chat.id, 'Кажется, что-то пошло не так...', reply_markup=removing_buttons)
        print('Ops...\n', ex)


@bot.message_handler(commands=['payforsub'])
def pay(message):
    with open('purchase_info.json', encoding='utf-8') as file:
        info = json.load(file)
        if 'test' in message.text:
            payment_token = info["TEST_PAYMENT_TOKEN"]
        else:
            payment_token = info["PAYMENT_TOKEN"]
        sub_info = info["subscription_info"]
        title = sub_info["title"]
        description = sub_info["description"]
        purchase_label = sub_info["purchase_label"]
        start_p = sub_info["start_p"]
        invoice_p = sub_info["invoice_p"]
        sub_price = sub_info["price"]

    price = types.LabeledPrice(label=purchase_label, amount=sub_price * 100)
    try:
        bot.send_invoice(message.chat.id,
                         title=title,
                         description=description,
                         provider_token=payment_token,
                         currency="rub",
                         prices=[price],
                         start_parameter=start_p,
                         invoice_payload=invoice_p)
    except Exception as ex:
        print('Проблема с платёжкой')
        print(ex)


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Возникла непредвиденная ошибка. Попробуйте позже")


@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    if not db.check_user(message.from_user.id):
        db.add_user(message.from_user.id, datetime.now().timestamp(), 0)
    db.upd_user(message.from_user.id, db.check_user_datetime(message.from_user.id) + int(30 * 24 * 60 * 60), 1)
    bot.send_message(message.chat.id, f"Платёж прошел успешно! "
                                      f"Сумма оплаты составила {message.successful_payment.total_amount / 100}"
                                      f" {message.successful_payment.currency}")


bot.add_custom_filter(telebot.custom_filters.StateFilter(bot))


@bot.message_handler(content_types=['text'],
                     func=lambda message: str(message.chat.id) != SUPPORT_CHAT and SUPPORT_CHAT != 'None')
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
        with open(Path.cwd() / 'messages' / 'impossible_write.txt', 'r', encoding='utf-8') as file:
            text = file.read() + datetime.fromtimestamp(info[0]).date().isoformat()
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=button)


def checking_subscription():
    current_date_time = datetime.now().timestamp()
    all_users = db.get_all()
    for i in all_users:
        if i[3]:
            if current_date_time > i[2]:  # конец подписки
                try:
                    normal_kick(i[1])
                    db.upd_user_status(i[1], 0)
                except Exception as ex:
                    print("Выгнать человека не удалось\n" + str(ex))
                with open(Path.cwd() / 'messages' / 'end_subscription_message.txt', 'r', encoding='utf-8') as file:
                    bot.send_message(LIST_ID, file.read(), parse_mode='Markdown',
                                     disable_web_page_preview=True)
            elif int(-1 * (i[2] / 86400) // 1 * -1) == 7:  # предупреждение за неделю
                with open(Path.cwd() / 'messages' / 'week_until_end_subscription_message.txt', 'r',
                          encoding='utf-8') as file:
                    bot.send_message(LIST_ID, file.read(), parse_mode='Markdown',
                                     disable_web_page_preview=True)
            elif int(-1 * (i[2] / 86400) // 1 * -1) == 3:  # предупреждение за три дня
                with open(Path.cwd() / 'messages' / 'three_days_until_end_subscription.txt', 'r',
                          encoding='utf-8') as file:
                    bot.send_message(LIST_ID, file.read(), parse_mode='Markdown',
                                     disable_web_page_preview=True)
            elif int(-1 * (i[2] / 86400) // 1 * -1) == 1:  # предупреждение за один день
                with open(Path.cwd() / 'messages' / 'day_until_end_subscription.txt', 'r', encoding='utf-8') as file:
                    bot.send_message(LIST_ID, file.read(), parse_mode='Markdown',
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
