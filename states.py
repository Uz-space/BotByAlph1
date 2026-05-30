from aiogram.fsm.state import State, StatesGroup

class Order(StatesGroup):
    amount = State()
    confirm = State()

class Feedback(StatesGroup):
    writing = State()

class Admin(StatesGroup):
    broadcast = State()
    price_crypto = State()
    price_buy = State()
    price_sell = State()
    reply_to = State()
