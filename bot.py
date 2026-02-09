import logging
import asyncio
import os
import html
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# --- НАСТРОЙКИ ---
API_TOKEN = '8274836392:AAHtEMyz06QkWAYQVq9xJ72k3G5u20el7hs'
CHANNEL_ID = '@SCHOOL4USI'
# Админ 8157915802 удален
ADMINS = [6790613456, 7037839535, 8083579876] 
BAN_FILE = "banned_users.txt"
STATS_FILE = "stats.txt"

bot = Bot(token=API_TOKEN, default_properties=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_spam_check = {}

for f_name in [BAN_FILE, STATS_FILE]:
    if not os.path.exists(f_name):
        with open(f_name, "w") as f: f.write("0" if f_name == STATS_FILE else "")

def get_banned_users():
    try:
        with open(BAN_FILE, "r") as f: return {int(line.strip()) for line in f if line.strip().isdigit()}
    except: return set()

def update_stats():
    try:
        with open(STATS_FILE, "r") as f: count = int(f.read().strip() or 0)
        with open(STATS_FILE, "w") as f: f.write(str(count + 1))
    except: pass

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👋 Бот активен. Пришли пост для предложки.")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id not in ADMINS: return
    total = open(STATS_FILE, "r").read().strip()
    banned = len(get_banned_users())
    await message.answer(f"📊 Статистика:\n✅ Опубликовано: {total}\n🚫 В бане: {banned}")

@dp.message(F.content_type.in_({'text', 'photo', 'video', 'video_note', 'voice', 'audio', 'document'}))
async def handle_suggestion(message: types.Message):
    user_id = message.from_user.id
    if user_id in get_banned_users(): return await message.answer("🚫 Вы заблокированы.")

    now = time.time()
    if user_id in user_spam_check and now - user_spam_check[user_id] < 10:
        return await message.answer("⚠️ Не спамьте.")
    user_spam_check[user_id] = now

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"pub_{user_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"rej_{user_id}")],
        [InlineKeyboardButton(text="🔍 Кто писал?", callback_data=f"who_{user_id}")],
        [InlineKeyboardButton(text="🚫 Бан", callback_data=f"ban_{user_id}")]
    ])

    for admin_id in ADMINS:
        try: await message.copy_to(admin_id, reply_markup=kb)
        except: continue
    await message.answer("✅ Отправлено модераторам!")

# --- КНОПКИ ---

@dp.callback_query(F.data.startswith("pub_"))
async def publish_post(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS: return
    try:
        # Публикуем в канал
        await callback.message.copy_to(CHANNEL_ID)
        update_stats()
        # НЕ удаляем кнопки, просто уведомляем админа
        await callback.answer("✅ Опубликовано в канал!", show_alert=False)
        # Опционально: можно добавить текст в сообщение админа, что пост уже выложен
        await callback.message.reply("📢 Этот пост уже опубликован.")
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)

@dp.callback_query(F.data.startswith("rej_"))
async def reject_post(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS: return
    user_id = callback.data.split("_")[1]
    try: await bot.send_message(user_id, "❌ Ваше сообщение отклонено.")
    except: pass
    await callback.message.delete()
    await callback.answer("Отклонено")

@dp.callback_query(F.data.startswith("who_"))
async def identify_user(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS: return
    user_id = callback.data.split("_")[1]
    await callback.answer("Ищу автора...")
    try:
        u = await bot.get_chat(user_id)
        res = (f"👤 {html.escape(u.full_name)}\n🔗 @{u.username or 'нет'}\n🆔 <code>{user_id}</code>\n"
               f"📝 {html.escape(u.bio or 'пусто')}\n👉 <a href='tg://user?id={user_id}'>ПРОФИЛЬ</a>")
    except:
        res = f"🆔 <code>{user_id}</code>\n⚠️ Скрыт. <a href='tg://user?id={user_id}'>ПЕРЕЙТИ</a>"
    # Отправляем инфо отдельным сообщением, чтобы не портить карточку модерации
    await bot.send_message(callback.from_user.id, res)

@dp.callback_query(F.data.startswith("ban_"))
async def ban_user(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS: return
    uid = callback.data.split("_")[1]
    with open(BAN_FILE, "a") as f: f.write(f"{uid}\n")
    try: await bot.send_message(uid, "🚫 Вы забанены.")
    except: pass
    await callback.message.delete()
    await callback.answer("Забанен")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
