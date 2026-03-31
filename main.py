import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.filters import CommandStart

# Bot tokeningiz
BOTTOKEN = "8296081142:AAH7gYb30yDEAhPU6Er7oQQcZnPWd19oSJ8"

bot = Bot(token=BOTTOKEN)
dp = Dispatcher()

# ===== SQLITE (XATONI TUZATUVCHI QISM) =====
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

# DIQQAT: Agar jadvalda user_id bo'lmasa, uni o'chirib yangidan yaratamiz
try:
    cursor.execute("SELECT user_id FROM users LIMIT 1")
except sqlite3.OperationalError:
    # Agar xato bersa (user_id yo'q bo'lsa), jadvalni yangilaymiz
    cursor.execute("DROP TABLE IF EXISTS users")
    conn.commit()

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

# ===== MATNLAR (O'ZBEK TILIDA) =====
txt = {
    'main_menu': "Bosh menyu",
    'admin_btn': "Admin rejim",
    'new_reg': "Yangi ro'yxatdan o'tish",
    'back': "Qaytish",
    'is_admin': "Siz allaqachon adminsiz",
    'enter_login': "Login kiriting:",
    'ask_name': "Ismingiz nima?",
    'ask_surname': "Familiyangizni kiriting:",
    'ask_phone': "Telefon raqamingizni yuboring:",
    'ask_course': "Kursni tanlang:",
    'success': "Siz muvaffaqiyatli ro'yxatdan o'tdingiz!\nAdmin javobini kuting.",
    'no_users': "Hozircha ro'yxatdan o'tganlar yo'q",
    'deleted': "✅ Foydalanuvchi o'chirildi"
}

user_states = {}

# ===== KLAVIATURALAR =====
def get_kb(kb_type="main"):
    if kb_type == "main":
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=txt['admin_btn']), KeyboardButton(text=txt['new_reg'])]
        ], resize_keyboard=True)
    elif kb_type == "back":
        return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=txt['back'])]], resize_keyboard=True)
    elif kb_type == "course":
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text='Ofis ilovalari')], [KeyboardButton(text='Ingliz tili')],
            [KeyboardButton(text='Rus tili')], [KeyboardButton(text='Matematika')],
            [KeyboardButton(text='Turk tili')], [KeyboardButton(text='Python dasturlash')],
            [KeyboardButton(text=txt['back'])]
        ], resize_keyboard=True)

# ===== HANDLERLAR =====

@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    user_states[user_id] = None
    await message.answer("Assalomu aleykum! Botimizga xush kelibsiz.", reply_markup=get_kb("main"))

@dp.message(F.text == txt['back'])
async def back_handler(message: Message):
    user_states[message.from_user.id] = None
    await message.answer(txt['main_menu'], reply_markup=get_kb("main"))

@dp.message(F.text == txt['admin_btn'])
async def admin_start(message: Message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM admins WHERE user_id=?", (user_id,))
    if cursor.fetchone():
        user_states[user_id] = "admin"
        await message.answer(txt['is_admin'], reply_markup=get_kb("main"))
    else:
        user_states[user_id] = "login"
        await message.answer(txt['enter_login'], reply_markup=get_kb("back"))

@dp.message(F.text == txt['new_reg'])
async def new_user(message: Message):
    user_states[message.from_user.id] = {"step": "name"}
    await message.answer(txt['ask_name'], reply_markup=get_kb("back"))

@dp.message()
async def main_handler(message: Message):
    user_id = message.from_user.id
    text = message.text
    state = user_states.get(user_id)

    if text == txt['back']: return

    if state == "login":
        if text == "stepadmin":
            user_states[user_id] = "password"
            await message.answer("Parolni kiriting:")
        else:
            await message.answer("Xato login!")

    elif state == "password":
        if text == "12345678":
            user_states[user_id] = "admin"
            cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
            conn.commit()
            await message.answer("Xush kelibsiz, Admin!", reply_markup=get_kb("main"))
        else:
            await message.answer("Xato parol!")

    elif state == "admin":
        if "Kurs" in text or text == "Admin rejim":
            cursor.execute("SELECT user_id, name, surname, phone, course FROM users WHERE name IS NOT NULL")
            rows = cursor.fetchall()
            if not rows:
                await message.answer(txt['no_users'])
            else:
                for r in rows:
                    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ O'chirish", callback_data=f"delete_{r[0]}")]])
                    await message.answer(f"👤 {r[1]} {r[2]}\n📞 {r[3]}\n📚 Kurs: {r[4]}", reply_markup=kb)

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
    print("Bot yoqildi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
