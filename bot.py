import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- НАСТРОЙКИ ---
API_TOKEN = '8274836392:AAHtEMyz06QkWAYQVq9xJ72k3G5u20el7hs'
CHANNEL_ID = '@SCHOOL4USI'
# Твои 4 админа
ADMINS = [6790613456, 7037839535, 8083579876, 8157915802]
BAN_FILE = "banned_users.txt"

RULES_TEXT = (
    "⚠️ **ПРАВИЛА КАНАЛА**\n\n"
    "📌 Канал не является официальным каналом школы\n"
    "📌 Все сообщения публикуются после модерации\n\n"
    "❌ **Запрещено:**\n"
    "— оскорбления и унижения\n"
    "— травля и призывы к ней\n"
    "— клевета и распространение слухов\n"
    "— деанонимизация\n\n"
    "🚫 Сообщения, нарушающие правила, не публикуются\n"
    "🚫 Авторы могут быть заблокированы"
)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- СИСТЕМА БАНА (Работа с файлом) ---
def get_banned_users():
    if not os.path.exists(BAN_FILE): return set()
    with open(BAN_FILE, "r") as f:
        return {int(line.strip()) for line in f if line.strip().isdigit()}

def add_to_ban(user_id):
    with open(BAN_FILE, "a") as f:
        f.write(f"{user_id}\n")

# --- ОБРАБОТЧИКИ КОМАНД ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"👋 Привет! Пришли сообщение (текст или фото) для публикации.\n\n{RULES_TEXT}", parse_mode="Markdown")

@dp.message(Command("rules"))
async def cmd_rules(message: types.Message):
    await message.answer(RULES_TEXT, parse_mode="Markdown")

@dp.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if message.from_user.id not in ADMINS: return
    args = message.text.split()
    if len(args) < 2: 
        return await message.answer("Используй: `/unban ID` (например /unban 1234567)")
    
    target_id = args[1].strip()
    if os.path.exists(BAN_FILE):
        with open(BAN_FILE, "r") as f:
            lines = f.readlines()
        with open(BAN_FILE, "w") as f:
            for line in lines:
                if line.strip() != target_id: f.write(line)
        await message.answer(f"✅ Пользователь `{target_id}` разблокирован.")

# --- ПРИЕМ СООБЩЕНИЙ ---

@dp.message(F.text | F.photo)
async def handle_suggestion(message: types.Message):
    if message.from_user.id in get_banned_users():
        return await message.answer("🚫 Вы заблокированы и не можете отправлять сообщения.")

    # Создаем кнопки для админов
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"pub_{message.from_user.id}")],
        [InlineKeyboardButton(text="🔍 Кто написал?", callback_data=f"who_{message.from_user.id}")],
        [InlineKeyboardButton(text="🚫 Бан", callback_data=f"ban_{message.from_user.id}")]
    ])

    # Рассылаем админам
    for admin_id in ADMINS:
        try:
            if message.text:
                await bot.send_message(admin_id, message.text, reply_markup=kb)
            elif message.photo:
                await bot.send_photo(admin_id, message.photo[-1].file_id, caption=message.caption, reply_markup=kb)
        except Exception as e:
            logging.error(f"Не удалось отправить админу {admin_id}: {e}")
    
    await message.answer("✅ Ваше сообщение отправлено администраторам на проверку!")

# --- ОБРАБОТКА КНОПОК ---

@dp.callback_query(F.data.startswith("pub_"))
async def publish_post(callback: CallbackQuery):
    try:
        if callback.message.text:
            await bot.send_message(CHANNEL_ID, callback.message.text)
        elif callback.message.photo:
            await bot.send_photo(CHANNEL_ID, callback.message.photo[-1].file_id, caption=callback.message.caption)
        
        # Убираем кнопки после публикации
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer("Опубликовано в канал!")
    except Exception as e:
        await callback.answer(f"Ошибка публикации: {e}", show_alert=True)

@dp.callback_query(F.data.startswith("who_"))
async def identify_user(callback: CallbackQuery):
    user_id = callback.data.split("_")[1]
    
    # Сразу отвечаем Телеграму, чтобы кнопка не зависала
    await callback.answer("Запрашиваю данные...")

    try:
        # Пытаемся получить данные профиля
        u = await bot.get_chat(user_id)
        name = u.full_name or "Не указано"
        username = f"@{u.username}" if u.username else "Отсутствует"
        bio = u.bio if u.bio else "Не заполнено"
        
        res = (
            f"📋 **ПОЛНАЯ КАРТОЧКА АВТОРА:**\n\n"
            f"👤 **Имя:** [{name}](tg://user?id={user_id})\n"
            f"🔗 **Юзернейм:** {username}\n"
            f"🆔 **ID:** `{user_id}`\n"
            f"📝 **О себе:** {bio}\n"
            f"📞 **Телефон:** Скрыт\n\n"
            f"💡 *Если ссылки не работают, значит у юзера закрытый профиль.*"
        )
    except Exception:
        # Если юзер скрыт или бот его "не видит"
        res = (
            f"🆔 **ID автора:** `{user_id}`\n\n"
            f"⚠️ **Профиль скрыт.** Данные (имя/био) недоступны, так как пользователь не в контактах бота.\n\n"
            f"🔗 [Ссылка на профиль](tg://user?id={user_id})"
        )

    await bot.send_message(callback.from_user.id, res, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("ban_"))
async def ban_user(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    add_to_ban(user_id)
    
    await bot.send_message(callback.from_user.id, f"🚫 Пользователь `{user_id}` заблокирован.")
    # Удаляем сообщение из чата админов, чтобы не мозолило глаза
    await callback.message.delete()
    await callback.answer("Забанен")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
