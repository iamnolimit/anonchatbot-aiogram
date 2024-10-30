from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

def gender_select():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Laki-laki", callback_data="gender_male")
    keyboard.button(text="Perempuan", callback_data="gender_female")
    return keyboard.as_markup()

def main_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Cari Teman Chat", callback_data="search_start")
    return keyboard.as_markup()

def search_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Berhenti Mencari", callback_data="search_stop")
    keyboard.adjust(1)
    return keyboard.as_markup(resize_keyboard=True)

def chating_menu():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text="Akhiri Percakapan")
    keyboard.button(text="Cari Teman Chat Baru")
    keyboard.adjust(1)
    return keyboard.as_markup(resize_keyboard=True)
