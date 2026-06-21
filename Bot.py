import asyncio
import logging
import random
import time
import aiohttp
from bs4 import BeautifulSoup

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = '8895349588:AAHt-0h3IRfMnogrHmHAr_YQj9d1T3voTcg'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    waiting_for_length = State()
    waiting_for_count = State()

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('🔍 ПОИСК'))
    return keyboard

VOWELS = "aeiou"
CONSONANTS = "bcdfghklmnprstvw"

def generate_random_username(length: int) -> str:
    while True:
        username = ""
        for i in range(length):
            if i % 2 == 0:
                username += random.choice(CONSONANTS)
            else:
                username += random.choice(VOWELS)
        if not any(username[i] == username[i+1] == username[i+2] for i in range(len(username) - 2)):
            return username

def get_rarity_level(username: str) -> str:
    length = len(username)
    if length <= 5:
        return "💠 Легенда"
    elif length <= 6:
        return "💎 Редкий"
    elif length <= 8:
        return "✨ Хороший"
    else:
        return "🔹 Обычный"

async def check_telegram_available(username: str) -> bool:
    url = f"https://t.me/{username}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status != 200:
                    return False
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                vcard = soup.find("div", class_="tgme_page_extra")
                if not vcard:
                    if "If you have Telegram, you can contact" in html or "View in Telegram" in html:
                        if "tgme_page_title" in html:
                            return False
                    return True
                return False
    except Exception:
        return False

async def check_fragment_available(username: str) -> bool:
    url = f"https://fragment.com/username/{username}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    html = await response.text()
                    if "Unknown" in html:
                        return True
                    if any(word in html for word in ["Taken", "Unavailable", "Buy", "TON", "Place bid", "Auction", "Sold"]):
                        return False
                return True
    except Exception:
        return True

async def check_username_available(username: str) -> bool:
    if not await check_telegram_available(username):
        return False
    if not await check_fragment_available(username):
        return False
    return True

@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    user_name = message.from_user.first_name or "Друг"
    text = (
        f"<b>💀 CHIGURH SEARCH 💀</b>\n\n"
        f"👤 Привет, {user_name}.\n\n"
        f"Я бесплатный искатель КРАСИВЫХ юзернеймов.\n"
        f"Проверяю Telegram + Fragment.\n"
        f"Без премиума. Без лимитов. Без жалости.\n\n"
        f"📜 <b>Команда:</b>\n"
        f"/search — начать поиск\n\n"
        f"<i>🛠 Разработчик: @Yeqqr</i>"
    )
    msg = await message.answer(text, reply_markup=get_main_keyboard())
    try:
        await msg.pin()
    except Exception:
        pass

@dp.message_handler(commands=['search'], state='*')
@dp.message_handler(lambda message: message.text == "🔍 ПОИСК", state='*')
async def cmd_search(message: types.Message):
    await Form.waiting_for_length.set()
    await message.answer("📏 Введи длину юзернейма (от 5 до 12):")

@dp.message_handler(state=Form.waiting_for_length)
async def process_length(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введи именно число от 5 до 12.")
        return
    length = int(message.text)
    if length < 5 or length > 12:
        await message.answer("❌ Длина должна быть от 5 до 12.")
        return
    await state.update_data(length=length)
    await Form.waiting_for_count.set()
    await message.answer("🔢 Сколько юзернеймов искать? (от 1 до 10):")

@dp.message_handler(state=Form.waiting_for_count)
async def process_count(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введи именно число от 1 до 10.")
        return
    count = int(message.text)
    if count < 1 or count > 10:
        await message.answer("❌ Количество должно быть от 1 до 10.")
        return
    
    data = await state.get_data()
    length = data['length']
    await state.finish()
    
    user_name = message.from_user.first_name or "Друг"
    status_msg = await message.answer("💀 <i>Ищу КРАСИВЫЕ свободные юзернеймы...</i>")
    
    start_time = time.time()
    found_usernames = []
    attempts = 0
    
    while len(found_usernames) < count:
        attempts += 1
        username = generate_random_username(length)
        if await check_username_available(username):
            found_usernames.append(username)
            if len(found_usernames) % 3 == 0:
                await status_msg.edit_text(f"💀 <i>Найдено {len(found_usernames)} из {count}...</i>")
        await asyncio.sleep(0.05)
    
    elapsed_time = time.time() - start_time
    speed = int(attempts / elapsed_time) if elapsed_time > 0 else 0
    
    await status_msg.delete()
    
    if found_usernames:
        text = (
            f"<b>💀 CHIGURH SEARCH 💀</b>\n\n"
            f"👤 Искал: {user_name}\n"
            f"📏 Длина: {length} | 🔢 Запрошено: {count}\n\n"
            f"✅ <b>Найдено: {len(found_usernames)}</b>\n\n"
        )
        for i, username in enumerate(found_usernames, 1):
            text += f"{i}. @{username}\n"
            text += f"   <a href='https://t.me/{username}'>t.me/{username}</a> | {get_rarity_level(username)}\n"
            if i < len(found_usernames):
                text += "\n"
        
        text += (
            f"\n📊 Проверено: {attempts} | ⏱ {elapsed_time:.1f}с | ⚡ {speed} юзернеймов/сек"
        )
        await message.answer(text, reply_markup=get_main_keyboard(), disable_web_page_preview=True)
    else:
        await message.answer(
            "❌ Ничего не найдено. Попробуй изменить длину или количество.",
            reply_markup=get_main_keyboard()
        )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
