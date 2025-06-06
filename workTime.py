import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InputFile, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from openpyxl import Workbook
from aiogram import types
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
from openpyxl.styles import Font, Border, Side
from aiogram.types import InputFile
from io import BytesIO 
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from datetime import datetime, timedelta


load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
DB_FILE = "worklogs.db"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, timeout=30)
dp = Dispatcher()

scheduler = AsyncIOScheduler(timezone=timezone("Asia/Yerevan"))
router = Router()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    await message.answer(
        "👋 Hello! Let's register and work together to keep everything running smoothly. 🚀"
    )
    await bot.send_sticker(user_id, "CAACAgIAAxkBAAIKK2gw-DloLNQ6m7XqMrW3YceaC4ltAAIMFgACrqswSOVzrIAwP7l1NgQ")


# ---------- SEND DAILY REMINDERS ----------
async def send_start_work_reminders():
    today = datetime.now().strftime("%d/%m/%Y")
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()

        for (user_id,) in users:
            async with db.execute("SELECT start_time, shift FROM work_logs WHERE user_id = ? AND date = ?", (user_id, today)) as cur:
                row = await cur.fetchone()
                start_time, shift = (row or (None, None))
                if (not start_time or start_time in ("", "OFF")) and shift in ("first", "middle", "second", "full"):
                    try:
                        await bot.send_message(user_id, "⏰ Reminder: Please start your work using /start_work.")
                        await bot.send_sticker(user_id, "CAACAgIAAxkBAAIKMWgw-5DZku7F6DDz7kmLClAdtmgvAALEAQACGBV4Ay23D3KHIlnkNgQ")
                    except Exception as e:
                        print(f"Start reminder failed for {user_id}: {e}")


async def send_end_work_reminders():
    today = datetime.now().strftime("%d/%m/%Y")
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()

        for (user_id,) in users:
            async with db.execute("SELECT end_time, shift FROM work_logs WHERE user_id = ? AND date = ?", (user_id, today)) as cur:
                row = await cur.fetchone()
                end_time, shift = (row or (None, None))
                if (not end_time or end_time in ("", "OFF")) and shift in ("first", "middle", "second", "full"):
                    try:
                        await bot.send_message(user_id, "⏰ Reminder: Please end your work using /end_work.")
                        await bot.send_sticker(user_id, "CAACAgIAAxkBAAIG0WgX9dhtJ7JL7_foAxQ3_QT8M4YJAAIDAAMU-sgfeoaGU4zV2H02BA")
                    except Exception as e:
                        print(f"End reminder failed for {user_id}: {e}")



async def send_full_shift_luck():
    today = datetime.now().strftime("%d/%m/%Y")
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()

        for (user_id,) in users:
            async with db.execute("SELECT shift FROM work_logs WHERE user_id = ? AND date = ?", (user_id, today)) as cur:
                row = await cur.fetchone()
                shift = row[0] if row else None

                if shift == "full":
                    try:
                        await bot.send_message(user_id, "👊 Good luck, bro! 💪🔥 Full shift warrior (08:00–00:00) 💼")
                        await bot.send_sticker(user_id, "CAACAgIAAxkBAAIKImgw9wABkVyP5aUEqlmZEq1w2dyGiwACBwADFPrIH2NKV7THPXVJNgQ")
                    except Exception as e:
                        logging.error(f"Fullshift message failed for {user_id}: {e}")

async def send_off_shift():
    today = datetime.now().strftime("%d/%m/%Y")
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()

        for (user_id,) in users:
            async with db.execute("SELECT shift FROM work_logs WHERE user_id = ? AND date = ?", (user_id, today)) as cur:
                row = await cur.fetchone()
                shift = row[0] if row else None

                if shift == "off":
                    try:
                        await bot.send_sticker(user_id, "CAACAgIAAxkBAAIKM2gw-79m051BaKPnp5ztU3yr6qqwAAIvAQACGBV4A1gAAdjLvMkb4zYE")
                    except Exception as e:
                        logging.error(f"Offshift message failed for {user_id}: {e}")

# ---------- DAILY REMINDER JOBS ----------

# Start reminders
scheduler.add_job(send_start_work_reminders, 'cron', hour=8, minute=0)
scheduler.add_job(send_start_work_reminders, 'cron', hour=12, minute=0)
scheduler.add_job(send_start_work_reminders, 'cron', hour=16, minute=0) 
scheduler.add_job(send_start_work_reminders, 'cron', hour=8, minute=0)  

# End reminders
scheduler.add_job(send_end_work_reminders, 'cron', hour=16, minute=0)    
scheduler.add_job(send_end_work_reminders, 'cron', hour=20, minute=0)   
scheduler.add_job(send_end_work_reminders, 'cron', hour=0, minute=0)     
scheduler.add_job(send_end_work_reminders, 'cron', hour=0, minute=0)      


scheduler.add_job(send_full_shift_luck, 'cron', hour=8, minute=30)

scheduler.add_job(send_off_shift, 'cron', hour=15, minute=30)

# ---------- DAILY INVENTORY REMAINDER ----------

async def send_low_stock_reminder():
    async with aiosqlite.connect(DB_FILE) as db:
        # Get all products below their defined threshold
        async with db.execute("""
            SELECT name, quantity, unit FROM products
            WHERE quantity <= threshold AND threshold > 0
        """) as cursor:
            low_stock_products = await cursor.fetchall()

        # Get all admin user IDs
        async with db.execute("SELECT admin_user_id FROM admins") as cursor:
            admins = await cursor.fetchall()

    if not low_stock_products or not admins:
        return  # No need to notify

    # Build reminder message
    reminder_msg = "⚠️ *Low Stock Alert:*\nThe following products are running low:\n\n"
    for name, quantity, unit in low_stock_products:
        quantity_display = int(quantity) if quantity == int(quantity) else quantity
        reminder_msg += f"• {name}: {quantity_display} {unit}\n"

    # Send to all admins
    for (admin_id,) in admins:
        await bot.send_message(admin_id, reminder_msg, parse_mode="Markdown")





# ---------- DB SETUP ----------
DB_FILE = 'work.db'


async def init_db():
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            # ---------- USERS ----------
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    station TEXT,
                    name TEXT,
                    hourly_rate REAL
                )
            """)

            # ---------- WORK LOGS ----------
            await db.execute("""
                CREATE TABLE IF NOT EXISTS work_logs (
                    user_id INTEGER,
                    station_name TEXT,
                    date TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    hours REAL,
                    shift TEXT,
                    PRIMARY KEY (user_id, date),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # ---------- ADMINS ----------
            await db.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    admin_user_id TEXT PRIMARY KEY,
                    name TEXT
                )
            """)

            await db.execute("""
                INSERT OR IGNORE INTO admins (admin_user_id, name) VALUES
                ('1291587607', 'Miostral')
            """)

            # ---------- STATIONS ----------
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stations (
                    station_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    hourly_rate REAL
                )
            """)

            await db.executemany("""
                INSERT OR IGNORE INTO stations (name, hourly_rate) VALUES (?, ?)
            """, [
                ('bar', 350),
                ('tiramisu', 700),
                ('kitchen', 600),
                ('manager', 500)
            ])

            # ---------- CATEGORIES ----------
            await db.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE
                )
            """)

            # ---------- PRODUCTS ----------
            await db.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    quantity REAL,
                    unit TEXT, -- g, kg, l, pcs
                    category_id INTEGER,
                    threshold REAL DEFAULT 0, -- used for low-stock alert
                    FOREIGN KEY (category_id) REFERENCES categories(category_id)
                )
            """)

            # ---------- STATION-PRODUCT RELATION ----------
            await db.execute("""
                CREATE TABLE IF NOT EXISTS station_products (
                    station_id INTEGER,
                    product_id INTEGER,
                    FOREIGN KEY (station_id) REFERENCES stations(station_id),
                    FOREIGN KEY (product_id) REFERENCES products(product_id),
                    PRIMARY KEY (station_id, product_id)
                )
            """)

            await db.commit()
    except Exception as e:
        print(f"❌ Error initializing database: {e}")


# ---------- BOT COMMANDS ----------




# ---------- REGISTER ----------

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_station = State()

@dp.message(Command("register"))
async def start_register(message: types.Message, state: FSMContext):
    await message.answer("Please provide your name:")
    await state.set_state(RegistrationStates.waiting_for_name)

@dp.message(StateFilter(RegistrationStates.waiting_for_name))
async def set_name(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    name = message.text

    await state.update_data(name=name)
    await message.answer(f"Hello {name}, now please select your station: 'bar', 'tiramisu', 'kitchen', or 'manager'.")
    await state.set_state(RegistrationStates.waiting_for_station)

@dp.message(StateFilter(RegistrationStates.waiting_for_station))
async def set_station(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    station = message.text.lower()

    if station not in ['bar', 'tiramisu', 'kitchen', 'manager']:
        await message.answer("⚠️ Invalid station. Please select one of: 'bar', 'tiramisu', 'kitchen', or 'manager'.")
        return

    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT hourly_rate FROM stations WHERE name = ?", (station,)) as cursor:
            row = await cursor.fetchone()
            hourly_rate = row[0]

        data = await state.get_data()
        name = data["name"]

        await db.execute("""
            INSERT OR REPLACE INTO users (user_id, name, station, hourly_rate)
            VALUES (?, ?, ?, ?)
        """, (user_id, name, station, hourly_rate))
        await db.commit()

    await message.answer(f"✅ Registered as {name} at {station.capitalize()} station ({hourly_rate} per hour).")
    await state.clear()


# ---------- REGISTER ADMIN----------
class RegistrationAdmin(StatesGroup):
    waiting_for_name = State() 
    waiting_for_admin_code = State() 



@dp.message(Command("register_admin"))
async def register_admin(message: types.Message, state: FSMContext):

    await message.answer("Please enter your name to register as an admin:")
    await state.set_state(RegistrationAdmin.waiting_for_name)

@dp.message(StateFilter(RegistrationAdmin.waiting_for_name))
async def ask_admin_code(message: types.Message, state: FSMContext):

    admin_name = message.text

    await state.update_data(admin_name=admin_name)
    await message.answer("🔐 Now, please enter the admin code:")
    await state.set_state(RegistrationAdmin.waiting_for_admin_code)

@dp.message(StateFilter(RegistrationAdmin.waiting_for_admin_code))
async def verify_admin_code(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = await state.get_data()
    admin_name = data.get("admin_name")

    if message.text.strip() == "0305":
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("INSERT OR IGNORE INTO admins (admin_user_id, name) VALUES (?, ?)", (user_id, admin_name))
            await db.commit()

        await message.answer(f"✅ {admin_name}, you are now registered as an admin.")
    else:
        await message.answer("❌ Incorrect code. Access denied.")
    await state.clear()




# ---------- CHANGE STATION ----------

@dp.message(Command("change_station"))
async def change_station(message: Message):
    user_id = str(message.from_user.id)
    await message.answer("Please select a new station: 'bar', 'tiramisu', 'kitchen', or 'manager'.")
    
    @dp.message_handler(lambda msg: msg.text.lower() in ['bar', 'tiramisu', 'kitchen', 'manager'])
    async def set_new_station(msg: Message):
        new_station = msg.text.lower()
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT hourly_rate FROM stations WHERE station_name = ?", (new_station,)) as cursor:
                row = await cursor.fetchone()
                hourly_rate = row[0]
            await db.execute("""
                UPDATE users SET station = ?, hourly_rate = ? WHERE user_id = ?
            """, (new_station, hourly_rate, user_id))
            await db.commit()
        
        await msg.answer(f"Your station has been updated to {new_station} with an hourly rate of {hourly_rate}.")

# --- Check if user is admin helper ---
async def is_admin(user_id: str) -> bool:
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT 1 FROM admins WHERE admin_user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone() is not None

# --- ADD CATEGORY ---
@dp.message(Command("add_category"))
async def add_category(message: Message):
    user_id = str(message.from_user.id)
    if not await is_admin(user_id):
        await message.answer("❌ You don't have permission to use this command.")
        return

    parts = message.text.strip().split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("⚠️ Please provide a category name: `/add_category CategoryName`")
        return
    
    category_name = parts[1].strip()
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category_name,))
        await db.commit()

    await message.answer(f"✅ Category *{category_name}* has been added.", parse_mode="Markdown")

# --- ADD PRODUCT ---
@dp.message(Command("add_product"))
async def add_product(message: Message):
    user_id = str(message.from_user.id)
    if not await is_admin(user_id):
        await message.answer("❌ You don't have permission to use this command.")
        return

    parts = message.text.strip().split(" ", 4)
    if len(parts) < 5:
        await message.answer("⚠️ Usage: /add_product Name Quantity Unit CategoryName")
        return

    _, name, quantity_str, unit, category_name = parts
    try:
        quantity = int(quantity_str)
    except ValueError:
        await message.answer("⚠️ Quantity must be an integer.")
        return

    async with aiosqlite.connect(DB_FILE) as db:
        # Get or create category
        cursor = await db.execute("SELECT category_id FROM categories WHERE name = ?", (category_name,))
        row = await cursor.fetchone()
        if row:
            category_id = row[0]
        else:
            cursor = await db.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
            category_id = cursor.lastrowid
            await db.commit()

        await db.execute(
            "INSERT INTO products (name, quantity, unit, category_id) VALUES (?, ?, ?, ?)",
            (name, quantity, unit, category_id)
        )
        await db.commit()

    await message.answer(f"✅ Product *{name}* added under category *{category_name}*.", parse_mode="Markdown")

# --- USE PRODUCT ---
@dp.message(Command("use_product"))
async def use_product(message: Message):
    user_id = str(message.from_user.id)
    if not await is_admin(user_id):
        await message.answer("❌ You don't have permission to use this command.")
        return

    args = message.text.strip().split()
    if len(args) != 3:
        await message.answer("⚠️ Usage: /use_product <product_id> <quantity_used>")
        return

    try:
        product_id = int(args[1])
        quantity_used = float(args[2])
    except ValueError:
        await message.answer("⚠️ Invalid product ID or quantity.")
        return

    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT quantity, unit FROM products WHERE product_id = ?", (product_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await message.answer("❌ Product not found.")
                return
            current_quantity, unit = row
            if quantity_used > current_quantity:
                await message.answer(f"❌ Insufficient stock. Only {current_quantity} {unit} available.")
                return
            new_quantity = current_quantity - quantity_used
            await db.execute("UPDATE products SET quantity = ? WHERE product_id = ?", (new_quantity, product_id))
            await db.commit()

    await message.answer(f"✅ Used {quantity_used} {unit} of product {product_id}. Remaining: {new_quantity} {unit}.")

# --- LIST PRODUCTS ---
@dp.message(Command("list_products"))
async def list_products(message: Message):
    user_id = str(message.from_user.id)
    if not await is_admin(user_id):
        await message.answer("❌ You don't have permission to use this command.")
        return

    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("""
            SELECT c.name, p.name, p.quantity, p.unit
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            ORDER BY c.name
        """) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await message.answer("❌ No products found.")
        return

    categories = {}
    for category, name, quantity, unit in rows:
        cat = category or "Uncategorized"
        categories.setdefault(cat, []).append(f"{name}: {int(quantity) if quantity==int(quantity) else quantity} {unit}")

    lines = ["📦 Product List:"]
    for cat, items in categories.items():
        lines.append(f"\n🗂 Category: {cat}")
        lines.extend(items)

    await message.answer("\n".join(lines))

# --- STATION PRODUCTS ---
@dp.message(Command("station_products"))
async def station_products(message: Message):
    user_id = str(message.from_user.id)
    if not await is_admin(user_id):
        await message.answer("❌ You don't have permission to use this command.")
        return

    args = message.text.strip().split()
    if len(args) != 2:
        await message.answer("⚠️ Usage: /station_products <station_id>")
        return

    try:
        station_id = int(args[1])
    except ValueError:
        await message.answer("⚠️ Station ID must be an integer.")
        return

    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("""
            SELECT p.name, p.quantity, p.unit FROM products p
            JOIN station_products sp ON p.product_id = sp.product_id
            WHERE sp.station_id = ?
        """, (station_id,)) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await message.answer(f"❌ No products found for station {station_id}.")
        return

    lines = [f"📦 Products at Station {station_id}:"]
    for name, quantity, unit in rows:
        lines.append(f"{name}: {quantity} {unit}")

    await message.answer("\n".join(lines))

# --- SHIFT ---

@dp.message(Command("set_shift"))
async def ask_shift(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("🕗 First Shift (08:00–16:00)", callback_data='shift_first')],
            [InlineKeyboardButton("🌆 Middle Shift (12:00–20:00)", callback_data='shift_middle')],
            [InlineKeyboardButton("🌃 Second Shift (16:00–00:00)", callback_data='shift_second')],
            [InlineKeyboardButton("💟 Full Shift (08:00–00:00)", callback_data='shift_full')],
            [InlineKeyboardButton("❌ Off Today", callback_data='shift_off')],
        ]
    )
    await message.answer("What shift are you working today?", reply_markup=keyboard)

# --- Handle Shift Selection ---
@dp.callback_query(F.data.startswith("shift_"))
async def handle_shift_selection(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    shift = callback_query.data.replace("shift_", "")
    today = datetime.now().strftime("%d/%m/%Y")

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT INTO work_logs (user_id, date, shift)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET shift=excluded.shift
        """, (user_id, today, shift))
        await db.commit()

    shift_names = {
        "first": "First Shift (08:00–16:00)",
        "middle": "Middle Shift (12:00–20:00)",
        "second": "Second Shift (16:00–00:00)",
        "full": "Full Shift (08:00–00:00)",
        "off": "Off Today"
    }

    await callback_query.answer(f"✅ Shift set to: {shift_names.get(shift, shift.capitalize())}")



async def bot_send_shift_question():
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕗 First Shift (08:00–16:00)", callback_data="shift_first")],
            [InlineKeyboardButton(text="🌆 Middle Shift (12:00–20:00)", callback_data="shift_middle")], 
            [InlineKeyboardButton(text="🌃 Second Shift (16:00–00:00)", callback_data="shift_second")],
            [InlineKeyboardButton(text="💟 Full Shift (08:00–00:00)", callback_data="shift_full")],
            [InlineKeyboardButton(text="❌ Off Today", callback_data="shift_off")]
        ]
    )

    for (user_id_raw,) in users:
        user_id = int(user_id_raw)
        try:
            await bot.send_message(user_id, "What shift are you working today?", reply_markup=keyboard)
        except Exception as e:
            print(f"Shift prompt failed for {user_id}: {e}")


scheduler.add_job(bot_send_shift_question, 'cron', hour=7, minute=0)




@dp.message(Command("shift_end"))
async def shift_end(message: Message):
    user_id = str(message.from_user.id)
    LOW_STOCK_THRESHOLD = 10  # define your low stock limit here
    MIN_LOW_STOCK_PRODUCTS = 2  # minimum products to trigger report

    # Check if user is admin
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT 1 FROM admins WHERE admin_user_id = ?", (user_id,)) as cursor:
            is_admin = await cursor.fetchone()

    if not is_admin:
        await message.answer("❌ You don't have permission to use this command.")
        return

    # Fetch products with low stock
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("""
            SELECT DISTINCT p.name, p.quantity, p.unit
            FROM products p
            JOIN station_products sp ON p.product_id = sp.product_id
            WHERE p.quantity <= ?
        """, (LOW_STOCK_THRESHOLD,)) as cursor:
            low_stock_products = await cursor.fetchall()

    if len(low_stock_products) >= MIN_LOW_STOCK_PRODUCTS:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        report_lines = [f"⚠️ Low Stock Products Report - {now_str}"]

        for name, quantity, unit in low_stock_products:
            quantity_display = int(quantity) if quantity == int(quantity) else quantity
            report_lines.append(f"{name}: {quantity_display} {unit}")

        report_lines.append(f"\nTotal Low Stock Products: {len(low_stock_products)}")
        await message.answer("\n".join(report_lines))
    else:
        # Send a reminder if fewer than 2 products are low
        await message.answer("🔔 Reminder: Low stock detected but fewer than 2 products. Please check inventory carefully.")






# ---------- START WORK ----------

async def register_user(user_id: str):
    try:
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT
                )
            """)
            await db.execute("""
                INSERT OR IGNORE INTO users (user_id) VALUES (?)
            """, (user_id,))
            await db.commit()
    except Exception as e:
        print(f"Error registering user {user_id}: {e}")
        raise


@dp.message(Command("start_work"))
async def start_work(message: Message):
    try:
        await register_user(str(message.from_user.id))

        user_id = str(message.from_user.id)
        today = datetime.now().strftime("%d/%m/%Y")
        now = datetime.now().strftime("%H:%M")

        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS work_logs (
                    user_id TEXT,
                    date TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    hours REAL,
                    PRIMARY KEY (user_id, date)
                )
            """)

            await db.execute("""
                INSERT OR IGNORE INTO work_logs (user_id, date, start_time, end_time, hours)
                VALUES (?, ?, ?, '', 0)
            """, (user_id, today, now))

            await db.execute("""
                UPDATE work_logs SET start_time = ? WHERE user_id = ? AND date = ?
            """, (now, user_id, today))
            await db.commit()

        await message.answer(f"🟢 Work started at {now} on {today}")
        await message.answer("vay araa eli gorc")

        try:
            await message.answer_sticker("CAACAgIAAxkBAAIGjmgX2XtiKGwc5UQTnEeLuY8-4C7IAAKsFAACAVTJSxbQNn7AYn0fNgQ")
        except Exception as e:
            print(f"Failed to send sticker: {e}")

    except Exception as e:
        print(f"Error in /start_work command: {e}")
        await message.answer("❌ Something went wrong. Please try again later.")


# ---------- END WORK ----------
@dp.message(Command("end_work"))
async def end_work(message: Message):
    user_id = str(message.from_user.id)
    now_time = datetime.now().strftime("%H:%M")

    async with aiosqlite.connect(DB_FILE) as db:
        # Get the most recent unfinished shift (no end_time yet)
        async with db.execute("""
            SELECT date, start_time FROM work_logs
            WHERE user_id = ? AND (end_time IS NULL OR end_time = '')
            ORDER BY date DESC LIMIT 1
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()

        if not row:
            await message.answer("⚠️ You must start work first using /start_work")
            return

        work_date, start_time_str = row
        start_time = datetime.strptime(start_time_str, "%H:%M")
        end_time = datetime.strptime(now_time, "%H:%M")

        # Handle overnight shift
        if end_time < start_time:
            end_time += timedelta(days=1)

        hours = round((end_time - start_time).seconds / 3600, 2)

        await db.execute("""
            UPDATE work_logs
            SET end_time = ?, hours = ?
            WHERE user_id = ? AND date = ?
        """, (now_time, hours, user_id, work_date))
        await db.commit()

    await message.answer(f"🔴 Work ended at {now_time}. Total worked: {hours} hours")

    try:
        await message.answer_sticker("CAACAgIAAxkBAAIGkGgX2aYJIzvH4fKF3hj0OpWnWw4RAALrFwACOFvQS2ytXSeKU4UdNgQ")
    except Exception as e:
        print(f"Failed to send sticker: {e}")



# ---------- REPORT ----------

@dp.message(Command("report"))
async def report(message: Message):
    user_id = str(message.from_user.id)
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT date, start_time, end_time, hours FROM work_logs WHERE user_id = ? ORDER BY date", (user_id,)) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await message.answer("❌ No data available.")
        return

    total = sum(row[3] for row in rows if isinstance(row[3], float))
    lines = ["🗓️ Work Report:"]
    for date, start, end, hours in rows:
        lines.append(f"{date} | Start: {start} | End: {end} | Hours: {hours}")
    lines.append(f"\n🧮 Total hours: {total}")
    await message.answer("\n".join(lines), parse_mode="Markdown")
    try:
        await message.answer_sticker("CAACAgIAAxkBAAIGjGgX2RIsRENWszvV4FcPXd9KUBR1AAI-FQAC4TvISyGu9Oi89CQPNgQ") 
    except Exception as e:
        print(f"Failed to send sticker: {e}")

# ---------- EXCEL EXPORT ----------

@dp.message(Command("export_excel"))
async def export_excel(message: Message):
    user_id = str(message.from_user.id)

    try:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT date, start_time, end_time, hours FROM work_logs WHERE user_id = ? ORDER BY date", (user_id,)) as cursor:
                logs = await cursor.fetchall()

            if not logs:
                await message.answer("❌ No work log data found.")
                return

        wb = Workbook()
        ws = wb.active
        ws.title = "Work Logs"

        # Headers
        headers = ["Date", "Start", "End", "Hours"]
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

        for row in logs:
            ws.append(row)

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        file = InputFile(output, filename=f"report_{user_id}.xlsx")
        await message.answer_document(file, caption="📊 Your work log report.")

    except Exception as e:
        await message.answer("❌ Failed to export Excel file.")
        print(f"Export error: {e}")
    
# ---------- MONTHLY SUMMARY ----------
async def send_monthly_summary():
    current_month = datetime.now().strftime("%m")
    current_year = datetime.now().strftime("%Y")

    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()

        for (user_id,) in users:
            async with db.execute("""
                SELECT SUM(hours) FROM work_logs 
                WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
            """, (user_id, current_month, current_year)) as cur:
                row = await cur.fetchone()
                total_hours = row[0] if row[0] else 0.0

            try:
                await bot.send_message(
                    user_id,
                    f"📆 *Monthly Summary*\nYou worked a total of *{total_hours} hours* in {datetime.now().strftime('%B')}.\nGreat job! 🎉",
                    parse_mode="Markdown"
                )

                await bot.send_sticker("CAACAgIAAxkBAAIGs2gX3i2qv6yzUW806VH5o4WatPONAAI2FgACIPchSJtXUTwXDwW5NgQ")
            except Exception as e:
                print(f"Failed to send summary to user {user_id}: {e}")

                    
scheduler.add_job(send_monthly_summary, 'cron', day='28-31', hour=7, minute=0, id="monthly_summary", misfire_grace_time=3600)

# ---------- OFF ----------
@dp.message(Command("off"))
async def mark_off_day(message: Message):
    user_id = str(message.from_user.id)
    args = message.text.strip().split()
    if len(args) == 1:
        off_date = datetime.now().strftime("%d/%m/%Y")
    elif len(args) == 2:
        try:
            datetime.strptime(args[1], "%d/%m/%Y")
            off_date = args[1]
        except ValueError:
            await message.answer("⚠️ Please use the format `/off dd/mm/yyyy`")
            return
    else:
        await message.answer("⚠️ Usage: `/off` or `/off dd/mm/yyyy`", parse_mode="Markdown")
        return

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT OR REPLACE INTO work_logs (user_id, date, start_time, end_time, hours)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, off_date, "OFF", "OFF", 0.0))
        await db.commit()

    await message.answer(f"✅ Marked {off_date} as an OFF day 🛌", parse_mode="Markdown")
    try:
        await message.answer_sticker("CAACAgIAAxkBAAIGlmgX2gpRBCe99llBp1SDW4D6Jhj_AALAFgAC-FLQS9CqJ2GwUsWCNgQ")
    except Exception as e:
        print(f"Failed to send sticker: {e}")

# ---------- EDIT ----------
@dp.message(Command("edit"))
async def edit_work_time(message: Message):
    user_id = str(message.from_user.id)
    args = message.text.strip().split()

    if len(args) != 4:
        await message.answer("⚠️ Usage: `/edit dd/mm/yyyy HH:MM HH:MM`", parse_mode="Markdown")
        return

    date_str, start_str, end_str = args[1], args[2], args[3]

    try:
        # Validate input formats
        datetime.strptime(date_str, "%d/%m/%Y")
        start_time = datetime.strptime(start_str, "%H:%M")
        end_time = datetime.strptime(end_str, "%H:%M")
    except ValueError:
        await message.answer("❌ Invalid format. Use: `/edit dd/mm/yyyy HH:MM HH:MM`", parse_mode="Markdown")
        return

    try:
        await message.answer_sticker("CAACAgIAAxkBAAIGmmgX2yYL9O67xwGszVzYV0GCavwCAALwFQACyjPZS806D2QrLIi2NgQ")
    except Exception as e:
        print(f"Failed to send sticker: {e}")

    # Handle overnight shift
    if end_time < start_time:
        end_time += timedelta(days=1)

    work_seconds = (end_time - start_time).total_seconds()
    work_hours = round(work_seconds / 3600, 2)

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT OR REPLACE INTO work_logs (user_id, date, start_time, end_time, hours)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, date_str, start_str, end_str, work_hours))
        await db.commit()

    await message.answer(
        f"✏️ Updated `{date_str}`:\n🕒 Start: `{start_str}`\n🕔 End: `{end_str}`\n📊 Total: *{work_hours} hours*",
        parse_mode="Markdown"
    )

# ---------- REMOVE ----------
@dp.message(Command("remove"))
async def remove_log(message: Message):
    user_id = str(message.from_user.id)
    args = message.text.strip().split()

    if len(args) != 2:
        await message.answer("⚠️ Usage: `/remove dd/mm/yyyy`", parse_mode="Markdown")
        return

    date_str = args[1]

    try:
        datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        await message.answer("❌ Invalid date format. Use: `/remove dd/mm/yyyy`", parse_mode="Markdown")
        return

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            DELETE FROM work_logs WHERE user_id = ? AND date = ?
        """, (user_id, date_str))
        await db.commit()

    await message.answer(f"🗑️ Removed work log for {date_str}")

# ---------- RESET ----------
@dp.message(Command("reset"))
async def confirm_reset(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yes, reset", callback_data="confirm_reset"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_reset")
            ]
        ]
    )
    await message.answer("⚠️ Are you sure you want to delete all your work logs?", reply_markup=keyboard)

@dp.callback_query(F.data == "confirm_reset")
async def handle_confirm_reset(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM work_logs WHERE user_id = ?", (user_id,))
        await db.commit()

    await callback.message.edit_text("🧹 All your work logs have been deleted.")

@dp.callback_query(F.data == "cancel_reset")
async def handle_cancel_reset(callback: CallbackQuery):
    await callback.message.edit_text("❌ Reset canceled. Your data is safe.")

# ---------- SET BOT COMMANDS ----------
async def set_bot_commands():
    commands = [
        BotCommand(command="/start_work", description="Start your work day"),
        BotCommand(command="/end_work", description="End your work day"),
        BotCommand(command="/report", description="Get your work report"),
        BotCommand(command="/export_excel", description="Export work log to Excel"),
        BotCommand(command="/off", description="Mark the day as an OFF day"),
        BotCommand(command="/edit", description="Edit work time for a specific day"),
        BotCommand(command="/remove", description="Remove a work log for a specific day"),
        BotCommand(command="/reset", description="Reset all your work logs"),
        BotCommand(command="/money", description="Calculate total earnings"),
        BotCommand(command="/help", description="Show this help message")
    ]
    await bot.set_my_commands(commands)


# ---------- HELP ----------
@dp.message(Command("help"))
async def help(message: Message):
    help_text = """
Here are the available commands:

/start_work - Start your work day
/end_work - End your work day
/report - Get your work report
/export_excel - Export your work logs to an Excel file
/off - Mark the day as an OFF day
/edit - Edit work time for a specific day
/remove - Remove a work log for a specific day
/reset - Reset all your work logs
/money - Calculate total money earned (700 per hour)

Use `/help` at any time to see this list again.
    """
    await message.answer(help_text.strip())
    try:
        await message.answer_sticker("CAACAgIAAxkBAAIGsWgX3dsOnPGpvk60Gnm7q8frI290AAIMFgACrqswSOVzrIAwP7l1NgQ")
    except Exception as e:
        print(f"Failed to send sticker: {e}")

# ---------- MONEY ----------
@dp.message(Command("money"))
async def calculate_money(message: Message):
    user_id = str(message.from_user.id)
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT station, hourly_rate FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await message.answer("❌ You must register first using /register.")
                return
            station, hourly_rate = row

        async with db.execute("SELECT SUM(hours) FROM work_logs WHERE user_id = ?", (user_id,)) as cursor:
            total_hours_row = await cursor.fetchone()
            total_hours = total_hours_row[0] if total_hours_row[0] else 0.0

        total_money = round(total_hours * hourly_rate, 2)
    await message.answer(
        f"💰 *Earnings Summary*\n"
        f"Station: *{station.capitalize()}*\n"
        f"Hourly Rate: *{hourly_rate}*\n"
        f"Total Hours Worked: *{total_hours}*\n"
        f"Total Earned: *{total_money}*",
        parse_mode="Markdown"
    )

    try:
        await message.answer_sticker("CAACAgIAAxkBAAIGr2gX3KpvVOhLrt0jMlHB89d6ghXLAAKwHwACydrQSoqdo0Ms-4qgNgQ")
    except Exception as e:
        print(f"Failed to send sticker: {e}")


@dp.message(F.sticker)
async def get_sticker_id(message: Message):
    await message.answer(f"🆔 Sticker file ID:\n`{message.sticker.file_id}`", parse_mode="Markdown")

# ---------- MAIN ----------
async def main():
    await init_db()
    await set_bot_commands()
    scheduler.start()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
