import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart

TOKEN = os.getenv(8274836392:AAHtEMyz06QkWAYQVq9xJ72k3G5u20el7hs)

bot = Bot(8274836392:AAHtEMyz06QkWAYQVq9xJ72k3G5u20el7hs)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(msg: Message):
    await msg.answer(
        "✉️ Отправь сообщение.\n"
        "Админы его увидят, в канале оно выйдет анонимно."
    )

@dp.message()
async def handle(msg: Message):
    await msg.answer("✅ Сообщение отправлено на модерацию.")

async def main():
    await dp.start_polling(bot)

asyncio.run(main())
