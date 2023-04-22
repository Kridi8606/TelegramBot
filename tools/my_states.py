from telebot.handler_backends import State, StatesGroup


class MyStates(StatesGroup):
    neutral = State()
    mailing_text = State()
    adding_button = State()
    button_text = State()
    button_link = State()
    final_approve = State()