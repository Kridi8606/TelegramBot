import json
import sqlite3
import time
import validators

import telebot
from telebot import types
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from config import BOT_TOKEN, DATABASE_FILE
from database.db import User_database

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(BOT_TOKEN, state_storage=state_storage)
db = User_database(DATABASE_FILE)


class MyStates(StatesGroup):
    neutral = State()
    mailing_text = State()
    adding_button = State()
    button_text = State()
    button_link = State()
    final_approve = State()


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
    bot.send_message(message.chat.id, 'Пришлите текст рассылки')
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
    except Exception:
        bot.send_message(message.chat.id, 'Кажется, что-то пошло не так...', reply_markup=removing_buttons)


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
    bot.send_invoice(message.chat.id,
                           title=title,
                           description=description,
                           provider_token=payment_token,
                           currency="rub",
                           prices=[price],
                           start_parameter=start_p,
                           invoice_payload=invoice_p)


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Возникла непредвиденная ошибка. Попробуйте позже")


@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    bot.send_message(message.chat.id, f"Платёж прошел успешно! "
                                      f"Сумма оплаты составила {message.successful_payment.total_amount / 100}"
                                      f" {message.successful_payment.currency}")


bot.add_custom_filter(telebot.custom_filters.StateFilter(bot))

if __name__ == "__main__":
    print("Бот запущен")
    bot.polling()
print('Бот остановлен')
