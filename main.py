import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.filters import CommandStart

BOTTOKEN = "8296081142:AAH7gYb30yDEAhPU6Er7oQQcZnPWd19oSJ8"

bot = Bot(token=BOTTOKEN)
dp = Dispatcher()

# ===== SQLITE =====
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Foydalanuvchilar jadvaliga 'lang' ustunini qo'shdik
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    lang TEXT DEFAULT 'uz',
    name TEXT,
    surname TEXT,
    phone TEXT,
    course TEXT
)
""")

cursor.execute("CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)")
conn.commit()

# ===== LUG'AT (TRANSLATIONS) =====
texts = {
    'uz': {
        'start': "Assalomu aleykum! Qaysi tilda davom ettiramiz?",
        'main_menu': "Bosh menyu",
        'admin_btn': "Admin rejim",
        'new_reg': "Yangi rejim",
        'back': "Qaytish",
        'is_admin': "Siz allaqachon adminsiz",
        'enter_login': "Login kiriting:",
        'ask_name': "Sizning ismingiz nima?",
        'ask_surname': "Familiyangizni kiriting:",
        'ask_phone': "Telefon raqamingiz:",
        'ask_course': "Kursni tanlang:",
        'success': "Siz kursga yozildingiz!\nAdmin javobini kuting.",
        'no_users': "Hali hech kim yo‘q",
        'deleted': "✅ Foydalanuvchi o‘chirildi"
    },
    'qr': {
        'start': "Assalawma áleykum! Qaysı tilde dawam etemiz?",
        'main_menu': "Bas menyu",
        'admin_btn': "Admin rejim",
        'new_reg': "Jańa rejim",
        'back': "Artqa qaytıw",
        'is_admin': "Siz artıqsha adminsiz",
        'enter_login': "Login kiritiń:",
        'ask_name': "Atıńız kim?",
        'ask_surname': "Familiyańızdı kiritiń:",
        'ask_phone': "Telefon nomerińiz:",
        'ask_course': "Kurstı saylań:",
        'success': "Siz kursqa jazıldıńız!\nAdmin juwabın kütiń.",
        'no_users': "Ele hesh kim joq",
        'deleted': "✅ Paydalanıwshı óshirildi"
    }
}

# ===== STATES =====
user_states = {}

# ===== FUNKSIYALAR =====
def get_lang(user_id):
    cursor.execute("SELECT lang FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else 'uz'

def get_kb(lang, type="main"):
    if type == "main":
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=texts[lang]['admin_btn']), KeyboardButton(text=texts[lang]['new_reg'])]
        ], resize_keyboard=True)
    elif type == "back":
        return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=texts[lang]['back'])]], resize_keyboard=True)
    elif type == "course":
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text='Ofis ilovalari')], [KeyboardButton(text='Ingiliz tili')],
            [KeyboardButton(text='Rus tili')], [KeyboardButton(text='Matematika')],
            [KeyboardButton(text='Turk tili')], [KeyboardButton(text='Python dasturi')],
            [KeyboardButton(text=texts[lang]['back'])]
        ], resize_keyboard=True)

# ===== START & LANGUAGE SELECTION =====
@dp.message(CommandStart())
async def start_handler(message: Message):
    lang_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'zbek tili 🇺🇿", callback_data="lang_uz")],
        [InlineKeyboardButton(text="Qoraqolpoq tili 🏗️", callback_data="lang_qr")]
    ])
    await message.answer(">> Assalomu aleykum! Qaysi tilda davom ettiramiz?\n>> Assalawma áleykum! Qaysı tilde dawam etemiz?", reply_markup=lang_kb)

@dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    cursor.execute("INSERT OR REPLACE INTO users (user_id, lang) VALUES (?, ?)", (user_id, lang))
    conn.commit()
    
    await callback.message.delete()
    await callback.message.answer(texts[lang]['main_menu'], reply_markup=get_kb(lang))
    await callback.answer()

# ===== QAYTISH =====
@dp.message(F.text.in_({"Qaytish", "Artqa qaytıw"}))
async def back_handler(message: Message):
    lang = get_lang(message.from_user.id)
    user_states[message.from_user.id] = None
    await message.answer(texts[lang]['main_menu'], reply_markup=get_kb(lang))

# ===== ADMIN START =====
@dp.message(F.text.in_({"Admin rejim"}))
async def admin_start(message: Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    cursor.execute("SELECT * FROM admins WHERE user_id=?", (user_id,))
    if cursor.fetchone():
        user_states[user_id] = "admin"
        await message.answer(texts[lang]['is_admin'])
    else:
        user_states[user_id] = "login"
        await message.answer(texts[lang]['enter_login'], reply_markup=get_kb(lang, "back"))

# ===== USER START =====
@dp.message(F.text.in_({"Yangi rejim", "Jańa rejim"}))
async def new_user(message: Message):
    lang = get_lang(message.from_user.id)
    user_states[message.from_user.id] = {"step": "name"}
    await message.answer(texts[lang]['ask_name'], reply_markup=get_kb(lang, "back"))

# ===== MAIN HANDLER =====
@dp.message()
async def handler(message: Message):
    user_id = message.from_user.id
    text = message.text
    state = user_states.get(user_id)
    lang = get_lang(user_id)

    if state == "login":
        if text == "stepadmin":
            user_states[user_id] = "password"
            await message.answer("Password?")
        else: await message.answer("Xato!")

    elif state == "password":
        if text == "12345678":
            user_states[user_id] = "admin"
            cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
            conn.commit()
            await message.answer("Welcome Admin!")

    elif state == "admin":
        if "Kursga yozilganlar" in text or "Kurs" in text:
            cursor.execute("SELECT user_id, name, surname, phone, course FROM users WHERE name IS NOT NULL")
            rows = cursor.fetchall()
            if not rows: await message.answer(texts[lang]['no_users'])
            else:
                for r in rows:
                    await message.answer(f"{r[1]} {r[2]}\n{r[3]}\n{r[4]}", 
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌", callback_data=f"delete_{r[0]}")]]))

    elif isinstance(state, dict):
        if state["step"] == "name":
            state["name"], state["step"] = text, "surname"
            await message.answer(texts[lang]['ask_surname'])
        elif state["step"] == "surname":
            state["surname"], state["step"] = text, "phone"
            await message.answer(texts[lang]['ask_phone'])
        elif state["step"] == "phone":
            state["phone"], state["step"] = text, "course"
            await message.answer(texts[lang]['ask_course'], reply_markup=get_kb(lang, "course"))
        elif state["step"] == "course":
            cursor.execute("UPDATE users SET name=?, surname=?, phone=?, course=? WHERE user_id=?", 
                           (state["name"], state["surname"], text, text, user_id))
            conn.commit()
            user_states[user_id] = None
            await message.answer(texts[lang]['success'], reply_markup=get_kb(lang))

@dp.callback_query(F.data.startswith("delete_"))
async def delete_user(callback: CallbackQuery):
    u_id = int(callback.data.split("_")[1])
    lang = get_lang(callback.from_user.id)
    cursor.execute("DELETE FROM users WHERE user_id=?", (u_id,))
    conn.commit()
    await callback.message.edit_text(texts[lang]['deleted'])

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
