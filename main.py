import telebot
from config import BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)


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


# @bot.message.hamdler()
# def leave(message):
#     print(message)


if __name__ == "__main__":
    print("Бот запущен")
    bot.polling()
print('Бот остановлен')