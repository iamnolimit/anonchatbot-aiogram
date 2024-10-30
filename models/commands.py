from aiogram import types

my_commands = [
    types.BotCommand(command="start", description="Mulai menggunakan bot"),
    types.BotCommand(command="link", description="Kirim link profil kamu"),
    types.BotCommand(command="search", description="Cari lawan bicara"),
    types.BotCommand(command="next", description="Ganti lawan bicara"),
    types.BotCommand(command="stop", description="Akhiri percakapan")
]
