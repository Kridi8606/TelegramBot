from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def creating_button(text, callback):
    markup = InlineKeyboardMarkup()
    btn = InlineKeyboardButton(text=text, callback_data=str(callback))
    markup.add(btn)
    return markup
