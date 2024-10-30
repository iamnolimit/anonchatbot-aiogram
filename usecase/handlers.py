from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message
from aiogram import Dispatcher, Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatType, ParseMode
from models.db import DB
from models.state import States
from models.kb import *
from models.redis import *
import os
from typing import Union
import asyncio

bot = Bot("7911131556:AAEGBfG5HMcfxhgtvlJQxD39FgYF_vVhZ8g")

dp = Dispatcher()
router = Router()
LOG_GRUP = -4568938746
ADMIN_IDS = [
    1259894923,
    1735180969,
    1054295664
]


@dp.message(CommandStart(), StateFilter(None))
async def start(msg: Message, state:FSMContext):
    if await DB.check_user(msg.from_user.id):
        await msg.answer(text=f"Halo {msg.from_user.first_name}", reply_markup=main_menu())
    else:
        await msg.answer(text="Halo, kamu pengguna baru jadi mari mendaftar")
        await msg.answer(text="Pilih jenis kelamin kamu", reply_markup=gender_select())
        await state.set_state(States.setgender)


@dp.message(Command("broadcast"), F.chat.type == ChatType.PRIVATE)
async def broadcast_command(message: Message, state: FSMContext):
    # Check if user is admin
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Maaf, kamu tidak memiliki akses untuk menggunakan perintah ini.")
        return
    
    await message.answer("Masukkan pesan yang ingin di broadcast:")
    await state.set_state(States.broadcast_message)

@dp.message(States.broadcast_message)
async def handle_broadcast(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await state.clear()
        return
    
    await state.clear()
    
    # Get confirmation first
    confirm_msg = await message.answer(
        f"Anda akan mengirim pesan broadcast ini:\n\n{message.text}\n\n"
        "Apakah Anda yakin ingin mengirim pesan ini ke semua pengguna?",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ Ya", callback_data="broadcast_confirm"),
                types.InlineKeyboardButton(text="❌ Tidak", callback_data="broadcast_cancel")
            ]
        ])
    )
    
    # Save the broadcast message and confirmation message ID in state
    await state.update_data(
        broadcast_text=message.text,
        confirm_msg_id=confirm_msg.message_id
    )
    await state.set_state(States.broadcast_confirm)

@dp.callback_query(States.broadcast_confirm)
async def process_broadcast_confirmation(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await state.clear()
        await callback.answer("Tidak memiliki akses")
        return

    if callback.data == "broadcast_cancel":
        await state.clear()
        await callback.message.edit_text("Broadcast dibatalkan.")
        return

    if callback.data == "broadcast_confirm":
        data = await state.get_data()
        broadcast_text = data['broadcast_text']
        
        # Edit confirmation message to show progress
        progress_msg = await callback.message.edit_text("Memulai broadcast...")
        
        # Get all users
        users = await DB.get_all_users()  # You need to implement this method in your DB class
        total_users = len(users)
        successful = 0
        failed = 0
        
        # Send messages with progress updates
        for i, user_id in enumerate(users, 1):
            try:
                await bot.send_message(user_id, broadcast_text)
                successful += 1
            except Exception as e:
                failed += 1
                # Log the error to admin group
                await bot.send_message(
                    LOG_GRUP,
                    f"Error broadcasting to user {user_id}: {str(e)}"
                )
            
            # Update progress every 10 users or at the end
            if i % 10 == 0 or i == total_users:
                await progress_msg.edit_text(
                    f"Broadcast dalam proses...\n"
                    f"Progress: {i}/{total_users}\n"
                    f"Berhasil: {successful}\n"
                    f"Gagal: {failed}"
                )
                await asyncio.sleep(0.05)  # Prevent flooding
        
        # Final report
        final_report = (
            "✅ Broadcast selesai!\n\n"
            f"Total pengguna: {total_users}\n"
            f"Berhasil terkirim: {successful}\n"
            f"Gagal terkirim: {failed}"
        )
        await progress_msg.edit_text(final_report)
        
        # Log the broadcast to admin group
        await bot.send_message(
            LOG_GRUP,
            f"📢 Broadcast Report\n\n"
            f"Admin: {callback.from_user.mention_html()}\n"
            f"Pesan: {broadcast_text}\n\n"
            f"Total pengguna: {total_users}\n"
            f"Berhasil: {successful}\n"
            f"Gagal: {failed}",
            parse_mode=ParseMode.HTML
        )
        
        await state.clear()

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

@dp.message(Command("stats"),F.chat.type == ChatType.GROUP)
async def show_stats(message: Message):
    # Check if user is authorized
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Maaf, kamu tidak memiliki akses untuk menggunakan perintah ini.")
        return
        
    stats = await DB.get_user_stats()
    
    text = (
        f"📊 Statistik Bot\n\n"
        f"Total Pengguna: {stats['total_users']}\n"
        f"\n👥 Berdasarkan Gender:\n"
        f"Laki-laki: {stats['gender_stats']['male']}\n"
        f"Perempuan: {stats['gender_stats']['female']}\n"
        f"\n📈 Statistik Usia:\n"
        f"Rata-rata: {stats['age_stats']['average']}\n"
        f"Termuda: {stats['age_stats']['youngest']}\n"
        f"Tertua: {stats['age_stats']['oldest']}\n"
        f"\n🔄 Distribusi Usia:\n"
        f"<18: {stats['age_distribution']['<18']}\n"
        f"18-25: {stats['age_distribution']['18-25']}\n"
        f"26-35: {stats['age_distribution']['26-35']}\n"
        f"36-50: {stats['age_distribution']['36-50']}\n"
        f">50: {stats['age_distribution']['>50']}"
    )
    
    await message.answer(text)

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
    await msg.answer(text="Percakapan berakhir", reply_markup=main_menu())
    await bot.send_message(chat_id=interlocutor, text="Percakapan berakhir", reply_markup=main_menu())
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
    
    # Format user's full name safely
    full_name = f"{msg.from_user.first_name}"
    if msg.from_user.last_name:
        full_name += f" {msg.from_user.last_name}"
    
    caption = f'<a href="tg://user?id={msg.from_user.id}">{full_name}</a>'
    await bot.send_photo(
        chat_id=LOG_GRUP,
        photo=msg.photo[-1].file_id,
        caption=caption,
        parse_mode=ParseMode.HTML
    )

@dp.message(States.chating, F.sticker)
async def sticker_chating(msg: Message):
    interlocutor = find_dialogue(msg.from_user.id)
    await bot.send_sticker(chat_id=interlocutor, sticker=msg.sticker.file_id)

@dp.message(States.chating, F.voice)
async def voice_chating(msg: Message):
    interlocutor = find_dialogue(msg.from_user.id)
    await bot.send_voice(chat_id=interlocutor, voice=msg.voice.file_id)
    
    # Format user's full name safely
    full_name = f"{msg.from_user.first_name}"
    if msg.from_user.last_name:
        full_name += f" {msg.from_user.last_name}"
    
    caption = f'<a href="tg://user?id={msg.from_user.id}">{full_name}</a>'
    await bot.send_voice(
        chat_id=LOG_GRUP,
        voice=msg.voice.file_id,
        caption=caption,
        parse_mode=ParseMode.HTML
    )

@dp.message(States.chating, F.video)
async def video_chating(msg: Message):
    interlocutor = find_dialogue(msg.from_user.id)
    await bot.send_video(chat_id=interlocutor, video=msg.video.file_id)
    
    # Format user's full name safely
    full_name = f"{msg.from_user.first_name}"
    if msg.from_user.last_name:
        full_name += f" {msg.from_user.last_name}"
    
    caption = f'<a href="tg://user?id={msg.from_user.id}">{full_name}</a>'
    await bot.send_video(
        chat_id=LOG_GRUP,
        video=msg.video.file_id,
        caption=caption,
        parse_mode=ParseMode.HTML
    )

@dp.message(States.chating)
async def error_chating(msg: Message):
    await msg.answer("❗PERHATIAN❗\nTipe data tidak didukung, pesan tidak terkirim")

@dp.message(StateFilter(None), F.chat.type == ChatType.PRIVATE)
async def warning(msg: Message, state: FSMContext):
    await msg.answer("Kamu belum memiliki lawan bicara. Untuk memulai ketik /start atau /search")
