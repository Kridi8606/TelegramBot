import telebot
from config import BOT_TOKEN, GROUP_ID, ADMINS_ID
from database.db import User_database, Hidden_continuation_database
from datetime import datetime
from tools.new_mailing_message_parser import new_mailing_message_parser
from tools.creating_button import creating_button
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


# @bot.message_handler(commands=['new_mailing'])
# def welcome_start(message):
#     try:
#         if message.from_user.id in ADMINS_ID:
#             result = new_mailing_message_parser(message.text)
#             if result['BUTTON_TEXT'] is not None:
#                 callback_database.add_button(result['SUB_EVENT'], result['NO_SUB_EVENT'], result['COND'])
#                 callback = callback_database.get_last_button()
#                 btn = creating_button(result['BUTTON_TEXT'], callback[0])
#                 # print(db.get_users())
#                 for user_id in db.get_users():
#                     try:
#                         bot.send_message(user_id[0], result['POST_TEXT'], reply_markup=btn, parse_mode='Markdown')
#                     except Exception as ex:
#                         print('Ops... Mailing error')
#                         print(ex)
#             else:
#                 # print(db.get_users())
#                 for user_id in db.get_users():
#                     try:
#                         bot.send_message(user_id[0], result['POST_TEXT'], parse_mode='Markdown')
#                     except Exception as ex:
#                         print('Ops... Mailing error')
#                         print(ex)
#     except Exception as ex:
#         print('Ops... Global Mailing error')
#         print(ex)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        # print(call)
        if callback_database.check_button(int(call.data)):
            callback, sub_event, no_sub_event, condition = callback_database.get_button(int(call.data))
            flag = True
            if condition != 'None':
                for i in condition.split(';'):
                    try:
                        # print(bot.get_chat_member(i, call.from_user.id))
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
            # print(bot.get_chat_member(message.chat.id, message.from_user.id))
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


if __name__ == "__main__":
    print("Бот запущен")
    bot.polling()
print('Бот остановлен')
