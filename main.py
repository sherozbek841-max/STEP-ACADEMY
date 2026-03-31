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
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    surname TEXT,
    phone TEXT,
    course TEXT
)
""")
cursor.execute("CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)")
conn.commit()

# ===== MATNLAR (FAQAT QORAQALPOQ TILIDA) =====
txt = {
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

user_states = {}

# ===== KLAVIATURALAR =====
def get_kb(type="main"):
    if type == "main":
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=txt['admin_btn']), KeyboardButton(text=txt['new_reg'])]
        ], resize_keyboard=True)
    elif type == "back":
        return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=txt['back'])]], resize_keyboard=True)
    elif type == "course":
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text='Ofis ilovalari')], [KeyboardButton(text='Ingiliz tili')],
            [KeyboardButton(text='Rus tili')], [KeyboardButton(text='Matematika')],
            [KeyboardButton(text='Turk tili')], [KeyboardButton(text='Python dasturi')],
            [KeyboardButton(text=txt['back'])]
        ], resize_keyboard=True)

# ===== START (TIL SO'RAMAYDI) =====
@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id
    # Foydalanuvchini bazaga qo'shib qo'yamiz (agar bo'lmasa)
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    
    await message.answer(txt['main_menu'], reply_markup=get_kb("main"))

# ===== QAYTISH =====
@dp.message(F.text == txt['back'])
async def back_handler(message: Message):
    user_states[message.from_user.id] = None
    await message.answer(txt['main_menu'], reply_markup=get_kb("main"))

# ===== ADMIN REJIM =====
@dp.message(F.text == txt['admin_btn'])
async def admin_start(message: Message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM admins WHERE user_id=?", (user_id,))
    if cursor.fetchone():
        user_states[user_id] = "admin"
        await message.answer(txt['is_admin'])
    else:
        user_states[user_id] = "login"
        await message.answer(txt['enter_login'], reply_markup=get_kb("back"))

# ===== YANGI REJIM (REGISTRATSIYA) =====
@dp.message(F.text == txt['new_reg'])
async def new_user(message: Message):
    user_states[message.from_user.id] = {"step": "name"}
    await message.answer(txt['ask_name'], reply_markup=get_kb("back"))

# ===== ASOSIY HANDLER =====
@dp.message()
async def main_handler(message: Message):
    user_id = message.from_user.id
    text = message.text
    state = user_states.get(user_id)

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
            await message.answer("Welcome Admin!", reply_markup=get_kb("main"))

    elif state == "admin":
        if "Kurs" in text or text == txt['admin_btn']:
            cursor.execute("SELECT user_id, name, surname, phone, course FROM users WHERE name IS NOT NULL")
            rows = cursor.fetchall()
            if not rows: await message.answer(txt['no_users'])
            else:
                for r in rows:
                    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌", callback_data=f"delete_{r[0]}")]])
                    await message.answer(f"👤 {r[1]} {r[2]}\n📞 {r[3]}\n📚 {r[4]}", reply_markup=kb)

    elif isinstance(state, dict):
        step = state.get("step")
        if step == "name":
            state["name"] = text
            state["step"] = "surname"
            await message.answer(txt['ask_surname'])
        elif step == "surname":
            state["surname"] = text
            state["step"] = "phone"
            await message.answer(txt['ask_phone'])
        elif step == "phone":
            state["phone"] = text
            state["step"] = "course"
            await message.answer(txt['ask_course'], reply_markup=get_kb("course"))
        elif step == "course":
            cursor.execute("UPDATE users SET name=?, surname=?, phone=?, course=? WHERE user_id=?", 
                           (state["name"], state["surname"], state["phone"], text, user_id))
            conn.commit()
            user_states[user_id] = None
            await message.answer(txt['success'], reply_markup=get_kb("main"))

@dp.callback_query(F.data.startswith("delete_"))
async def delete_user(callback: CallbackQuery):
    u_id = int(callback.data.split("_")[1])
    cursor.execute("DELETE FROM users WHERE user_id=?", (u_id,))
    conn.commit()
    await callback.message.edit_text(txt['deleted'])

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
