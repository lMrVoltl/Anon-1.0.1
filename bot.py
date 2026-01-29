import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- НАСТРОЙКИ ---
API_TOKEN = '8274836392:AAHtEMyz06QkWAYQVq9xJ72k3G5u20el7hs'
CHANNEL_ID = '@SCHOOL4USI'
ADMINS = [6790613456, 7037839535, 8083579876]
BAN_FILE = "banned_users.txt"

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ФУНКЦИИ БАЗЫ ДАННЫХ ---
def get_banned_users():
    if not os.path.exists(BAN_FILE):
        return set()
    with open(BAN_FILE, "r") as f:
        return {int(line.strip()) for line in f if line.strip().isdigit()}

def add_to_ban(user_id):
    with open(BAN_FILE, "a") as f:
        f.write(f"{user_id}\n")

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👋 Привет! Отправь мне текст или фото, и я анонимно предложу это в канал.")

@dp.message(F.text | F.photo)
async def handle_suggestion(message: types.Message):
    if message.from_user.id in get_banned_users():
        return await message.answer("🚫 Вы заблокированы в этом боте.")

    # Создаем кнопки для админов
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"pub_{message.from_user.id}")],
        [InlineKeyboardButton(text="🔍 Кто написал?", callback_data=f"who_{message.from_user.id}")],
        [InlineKeyboardButton(text="🚫 Бан", callback_data=f"ban_{message.from_user.id}")]
    ])

    # Рассылка админам
    for admin_id in ADMINS:
        try:
            if message.text:
                await bot.send_message(admin_id, f"📥 **Новое предложение:**\n\n{message.text}", reply_markup=kb)
            elif message.photo:
                await bot.send_photo(admin_id, message.photo[-1].file_id, caption=f"📥 **Новое фото:**\n{message.caption or ''}", reply_markup=kb)
        except Exception as e:
            logging.error(f"Ошибка отправки админу {admin_id}: {e}")

    await message.answer("✅ Ваше сообщение отправлено администраторам!")

@dp.callback_query(F.data.startswith("pub_"))
async def publish_post(callback: CallbackQuery):
    # Публикация в канал (без кнопок и лишнего текста)
    if callback.message.text:
        text = callback.message.text.replace("📥 Новое предложение:\n\n", "")
        await bot.send_message(CHANNEL_ID, text)
    elif callback.message.photo:
        caption = callback.message.caption.replace("📥 Новое фото:\n", "")
        await bot.send_photo(CHANNEL_ID, callback.message.photo[-1].file_id, caption=caption)
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(callback.from_user.id, "✅ Опубликовано в канал.")
    await callback.answer()

@dp.callback_query(F.data.startswith("who_"))
async def identify_user(callback: CallbackQuery):
    user_id = callback.data.split("_")[1]
    await bot.send_message(callback.from_user.id, f"👤 Автор поста: [Ссылка на профиль](tg://user?id={user_id})\nID: `{user_id}`", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("ban_"))
async def ban_user(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    add_to_ban(user_id)
    await bot.send_message(callback.from_user.id, f"🚫 Пользователь {user_id} заблокирован.")
    await callback.message.delete()
    await callback.answer()

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
