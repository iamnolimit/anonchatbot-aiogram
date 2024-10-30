from aiogram.filters import CommandStart,Command,StateFilter
from aiogram.types import Message
from aiogram import Dispatcher, Router, F,types,Bot
from aiogram.fsm.context import FSMContext
from models.db import DB
from models.state import States
from models.kb import *
from models.redis import *
import os
from typing import Union

bot = Bot("7911131556:AAEGBfG5HMcfxhgtvlJQxD39FgYF_vVhZ8g")

dp = Dispatcher()
router = Router()
LOG_GRUP = -1002125363162


@dp.message(CommandStart(), StateFilter(None))
async def start(msg: Message, state:FSMContext):
    if await DB.check_user(msg.from_user.id):
        await msg.answer(text=f"Halo {msg.from_user.first_name}", reply_markup=main_menu())
    else:
        await msg.answer(text="Halo, kamu pengguna baru jadi mari mendaftar")
        await msg.answer(text="Pilih jenis kelamin kamu", reply_markup=gender_select())
        await state.set_state(States.setgender)

@dp.callback_query(States.setgender, F.data.startswith("gender_"))
async def setgender(cb: types.CallbackQuery,state:FSMContext):
    data = cb.data
    _,gender = data.split("_")
    await state.update_data(gender=gender)
    await cb.message.answer("Masukkan usia kamu")
    await state.set_state(States.setage)

@dp.message(States.setage)
async def setage(msg:Message,state:FSMContext):
    try:
        age = int(msg.text)
    except ValueError:
        await msg.answer("Terjadi kesalahan, masukkan usia menggunakan angka")
        await msg.answer("Masukkan usia kamu")
        message = await dp.wait_for(types.Message, timeout=60)   #KOSTIL
        await setage(msg,state)

    payload = await state.get_data()
    gender = payload["gender"]
    await DB.create_user(msg.from_user.id,age,gender)
    if gender == "male":
        gender = "laki-laki"
    else:
        gender = "perempuan"
    await msg.answer(f"Data kamu berhasil disimpan.\nUsia: {age}\nJenis Kelamin: {gender}")
    await state.clear()

@dp.message(F.text == "/search", StateFilter(None))
@dp.callback_query(F.data == "search_start", StateFilter(None))
async def search_start(query_or_message: Union[types.CallbackQuery, Message], state:FSMContext):
    await state.set_state(States.searching)
    msg = query_or_message
    id = query_or_message.from_user.id
    if isinstance(query_or_message, types.CallbackQuery):
        msg = query_or_message.message
    add_in_queue(id)
    await msg.answer("Sedang mencari lawan bicara", reply_markup=search_menu())
    if check_queue():
        interlocutor = get_interlocutor(id)
        create_dialogue(id,interlocutor)
        text = "Lawan bicara ditemukan\n/stop untuk mengakhiri percakapan\n/next untuk mencari lawan bicara baru\n/link untuk membagikan link profil kamu"
        await msg.answer(text)
        await bot.send_message(chat_id=interlocutor, text=text)
        await state.set_state(States.chating)
        await dp.fsm.get_context(bot, user_id=interlocutor, chat_id=interlocutor).set_state(States.chating)

@dp.callback_query(F.data == "search_stop",States.searching)
async def search_stop(cb: types.CallbackQuery, state:FSMContext):
    await cb.message.answer(text="Pencarian dihentikan")
    del_from_queue(cb.from_user.id)
    await state.clear()

@dp.message(States.searching)
async def search_error(msg: Message):
    await msg.answer("Kamu sedang dalam pencarian lawan bicara", reply_markup=search_menu())

@dp.message(States.chating, lambda m: m.text == "/stop")
async def stop_chating(msg: Message):
    interlocutor = find_dialogue(msg.from_user.id)
    await msg.answer(text="Percakapan berakhir")
    await bot.send_message(chat_id=interlocutor, text="Percakapan berakhir")
    del_dialogue(msg.from_user.id, interlocutor)
    await dp.fsm.get_context(bot, user_id=interlocutor, chat_id=interlocutor).clear()
    await dp.fsm.get_context(bot, user_id=msg.from_user.id, chat_id=msg.from_user.id).clear()

@dp.message(States.chating, F.text == "/next")
async def next_chatting(msg: Message, state: FSMContext):
    await stop_chating(msg)
    await state.set_state(States.searching)
    add_in_queue(msg.from_user.id)
    await msg.answer("Sedang mencari lawan bicara", reply_markup=search_menu())
    if check_queue():
        interlocutor = get_interlocutor(msg.from_user.id)
        create_dialogue(msg.from_user.id,interlocutor)
        text = "Lawan bicara ditemukan\n/stop untuk mengakhiri percakapan\n/next untuk mencari lawan bicara baru\n/link untuk membagikan link profil kamu"
        await msg.answer(text)
        await bot.send_message(chat_id=interlocutor, text=text)
        await state.set_state(States.chating)
        await dp.fsm.get_context(bot, user_id=interlocutor, chat_id=interlocutor).set_state(States.chating)

@dp.message(States.chating, F.text == "/link")
async def link_chating(msg: Message, state: FSMContext):
    interlocutor = find_dialogue(msg.from_user.id)
    await bot.send_message(chat_id=interlocutor, text=f"Perhatian, lawan bicara mengirimkan link profilnya!!!\nhttps://t.me/{msg.from_user.username}")
    await msg.answer("Perhatian, lawan bicara telah menerima link profil kamu!!!")

@dp.message(States.chating, F.text)
async def chating(msg: Message):
    interlocutor = find_dialogue(msg.from_user.id)
    await bot.send_message(chat_id=interlocutor, text=msg.text)

@dp.message(States.chating, F.photo)
async def img_chating(msg: Message):
    interlocutor = find_dialogue(msg.from_user.id)
    await bot.send_photo(chat_id=interlocutor, photo=msg.photo[-1].file_id)
    await bot.send_photo(chat_id=LOG_GRUP, photo=msg.photo[-1].file_id)

@dp.message(States.chating, F.sticker)
async def sticker_chating(msg:Message):
    interlocutor = find_dialogue(msg.from_user.id)
    await bot.send_sticker(chat_id=interlocutor, sticker=msg.sticker.file_id)

@dp.message(States.chating, F.voice)
async def voice_chating(msg: Message):
    interlocutor = find_dialogue(msg.from_user.id)
    await bot.send_voice(chat_id=interlocutor, voice=msg.voice.file_id)
    await bot.send_voice(chat_id=LOG_GRUP, voice=msg.voice.file_id)

@dp.message(States.chating, F.video)
async def video_chating(msg: Message):
    interlocutor = find_dialogue(msg.from_user.id)
    await bot.send_video(chat_id=interlocutor, video=msg.video.file_id)
    await bot.send_video(chat_id=LOG_GRUP, video=msg.video.file_id)

@dp.message(States.chating)
async def error_chating(msg: Message):
    await msg.answer("❗PERHATIAN❗\nTipe data tidak didukung, pesan tidak terkirim")

@dp.message(StateFilter(None))
async def warning(msg:Message,state:FSMContext):
    await msg.answer("Kamu belum memiliki lawan bicara. Untuk memulai ketik /start atau /search")
