from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

class States(StatesGroup):
    setgender = State()
    setage = State()
    chating = State()
    searching = State()
    broadcast_message = State()
    broadcast_confirm = State()
# STATES = States()
