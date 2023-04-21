from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

Start_markup = InlineKeyboardMarkup()
btn1 = InlineKeyboardButton(text='Чат поддержки', callback_data='start_markup_support_chat')
btn2 = InlineKeyboardButton(text='Скрыть', callback_data='unseen')
Start_markup.add(btn1, btn2)