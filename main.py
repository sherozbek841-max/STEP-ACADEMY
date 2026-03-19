import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

BOTTOKEN = "8296081142:AAH7gYb30yDEAhPU6Er7oQQcZnPWd19oSJ8"

bot = Bot(token=BOTTOKEN)
dp = Dispatcher()

# ===== SQLITE =====
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    surname TEXT,
    phone TEXT,
    course TEXT
)
""")

# Admins table
cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY
)
""")

conn.commit()

# ===== STATES =====
user_states = {}

# ===== KEYBOARDS =====
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Admin rejim'), KeyboardButton(text='Yangi rejim')],
    ],
    resize_keyboard=True
)

back_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Qaytish')],
    ],
    resize_keyboard=True
)

course_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Ofis ilovalari')],
        [KeyboardButton(text='Ingiliz tili')],
        [KeyboardButton(text='Rus tili')],
        [KeyboardButton(text='Matematika')],
        [KeyboardButton(text='Turk tili')],
        [KeyboardButton(text='Python dasturi')],
        [KeyboardButton(text='Qaytish')],
    ],
    resize_keyboard=True
)

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Kursga yozilganlar')],
        [KeyboardButton(text='Qaytish')],
    ],
    resize_keyboard=True
)

# ===== START =====
@dp.message(CommandStart())
async def start_handler(message: Message):
    user_states[message.from_user.id] = None
    await message.answer(">> Assalomu aleykum!", reply_markup=main_kb)

# ===== QAYTISH =====
@dp.message(F.text == "Qaytish")
async def back_handler(message: Message):
    user_states[message.from_user.id] = None
    await message.answer(">> Bosh menyu", reply_markup=main_kb)

# ===== ADMIN START =====
@dp.message(F.text == "Admin rejim")
async def admin_start(message: Message):
    user_id = message.from_user.id

    cursor.execute("SELECT * FROM admins WHERE user_id=?", (user_id,))
    admin = cursor.fetchone()

    if admin:
        user_states[user_id] = "admin"
        await message.answer(">> Siz allaqachon adminsiz", reply_markup=admin_kb)
    else:
        user_states[user_id] = "login"
        await message.answer(">> Login kiriting:", reply_markup=back_kb)

# ===== USER START =====
@dp.message(F.text == "Yangi rejim")
async def new_user(message: Message):
    user_states[message.from_user.id] = {"step": "name"}
    await message.answer(">> Sizning ismingiz nima?", reply_markup=back_kb)

# ===== MAIN HANDLER =====
@dp.message()
async def handler(message: Message):
    user_id = message.from_user.id
    text = message.text
    state = user_states.get(user_id)

    # ===== LOGIN =====
    if state == "login":
        if text == "stepadmin":
            user_states[user_id] = "password"
            await message.answer(">> Parol kiriting:", reply_markup=back_kb)
        else:
            await message.answer(">> Login xato!")

    # ===== PASSWORD =====
    elif state == "password":
        if len(text) < 8 or text != "12345678":
            await message.answer(">> Parol xato!")
        else:
            user_states[user_id] = "admin"

            # SAVE ADMIN TO DB
            cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
            conn.commit()

            await message.answer(">> Xush kelibsiz Admin!", reply_markup=admin_kb)

    # ===== ADMIN PANEL =====
    elif state == "admin":
        if text == "Kursga yozilganlar":
            cursor.execute("SELECT name, surname, phone, course FROM users")
            rows = cursor.fetchall()

            if not rows:
                await message.answer(">> Hali hech kim yo‘q")
            else:
                result = ">> Ro‘yxat:\n\n"
                for r in rows:
                    result += f"{r[0]} {r[1]}\n{r[2]}\n{r[3]}\n\n"
                await message.answer(result)

    # ===== USER REGISTRATION =====
    elif isinstance(state, dict):

        if state["step"] == "name":
            state["name"] = text
            state["step"] = "surname"
            await message.answer(">> Familiyangizni kiriting:")

        elif state["step"] == "surname":
            state["surname"] = text
            state["step"] = "phone"
            await message.answer(">> Telefon raqamingiz:")

        elif state["step"] == "phone":
            state["phone"] = text
            state["step"] = "course"
            await message.answer(">> Kursni tanlang:", reply_markup=course_kb)

        elif state["step"] == "course":
            state["course"] = text

            # SAVE USER
            cursor.execute(
                "INSERT INTO users (name, surname, phone, course) VALUES (?, ?, ?, ?)",
                (state["name"], state["surname"], state["phone"], state["course"])
            )
            conn.commit()

            user_states[user_id] = None

            await message.answer(
                ">> Siz kursga yozildingiz!\nAdmin javobini kuting.",
                reply_markup=main_kb
            )

# ===== RUN =====
async def main():
    print("BOT ISHLAYAPTI!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())