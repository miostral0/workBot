import os
import logging
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, InputFile, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from openpyxl import Workbook
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from openpyxl.styles import Font, Border, Side
from io import BytesIO 
from aiogram import Router
from databases import Database
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side
from io import BytesIO
from aiogram.types import BufferedInputFile



load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
database = Database(DATABASE_URL)

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

    try:
        await database.connect()
        
        users = await database.fetch_all("SELECT user_id FROM users")
        
        for user in users:
            user_id = user["user_id"]
            row = await database.fetch_one(
                "SELECT start_time, shift FROM work_logs WHERE user_id = :user_id AND date = :date",
                values={"user_id": user_id, "date": today}
            )

            start_time = row["start_time"] if row else None
            shift = row["shift"] if row else None

            if (not start_time or start_time in ("", "OFF")) and shift in ("first", "middle", "second", "full"):
                try:
                    await bot.send_message(user_id, "⏰ Reminder: Please start your work using /start_work.")
                    await bot.send_sticker(user_id, "CAACAgIAAxkBAAIKMWgw-5DZku7F6DDz7kmLClAdtmgvAALEAQACGBV4Ay23D3KHIlnkNgQ")
                except Exception as e:
                    print(f"Start reminder failed for {user_id}: {e}")

        await database.disconnect()

    except Exception as e:
        print(f"❌ Error in send_start_work_reminders: {e}")




async def send_end_work_reminders():
    today = datetime.now().strftime("%d/%m/%Y")
    query_users = "SELECT user_id FROM users"
    query_work_logs = "SELECT end_time, shift FROM work_logs WHERE user_id = :user_id AND date = :date"

    try:
        users = await database.fetch_all(query=query_users)

        for user in users:
            user_id = user["user_id"]
            row = await database.fetch_one(query=query_work_logs, values={"user_id": user_id, "date": today})

            end_time, shift = (row["end_time"], row["shift"]) if row else (None, None)

            if (not end_time or end_time in ("", "OFF")) and shift in ("first", "middle", "second", "full"):
                try:
                    await bot.send_message(user_id, "⏰ Reminder: Please end your work using /end_work.")
                    await bot.send_sticker(user_id, "CAACAgIAAxkBAAIG0WgX9dhtJ7JL7_foAxQ3_QT8M4YJAAIDAAMU-sgfeoaGU4zV2H02BA")
                except Exception as e:
                    print(f"End reminder failed for {user_id}: {e}")

    except Exception as e:
        print(f"❌ Error in send_end_work_reminders: {e}")


async def send_full_shift_luck():
    today = datetime.now().strftime("%d/%m/%Y")
    query_users = "SELECT user_id FROM users"
    query_shift = "SELECT shift FROM work_logs WHERE user_id = :user_id AND date = :date"

    try:
        users = await database.fetch_all(query=query_users)

        for user in users:
            user_id = user["user_id"]
            row = await database.fetch_one(query=query_shift, values={"user_id": user_id, "date": today})
            shift = row["shift"] if row else None

            if shift == "full":
                try:
                    await bot.send_message(user_id, "👊 Good luck, bro! 💪🔥 Full shift warrior (08:00–00:00) 💼")
                    await bot.send_sticker(user_id, "CAACAgIAAxkBAAIKImgw9wABkVyP5aUEqlmZEq1w2dyGiwACBwADFPrIH2NKV7THPXVJNgQ")
                except Exception as e:
                    logging.error(f"Fullshift message failed for {user_id}: {e}")

    except Exception as e:
        logging.error(f"Error in send_full_shift_luck: {e}")



async def send_off_shift():
    today = datetime.now().strftime("%d/%m/%Y")
    query_users = "SELECT user_id FROM users"
    query_shift = "SELECT shift FROM work_logs WHERE user_id = :user_id AND date = :date"

    try:
        users = await database.fetch_all(query=query_users)

        for user in users:
            user_id = user["user_id"]
            row = await database.fetch_one(query=query_shift, values={"user_id": user_id, "date": today})
            shift = row["shift"] if row else None

            if shift == "off":
                try:
                    await bot.send_sticker(user_id, "CAACAgIAAxkBAAIKM2gw-79m051BaKPnp5ztU3yr6qqwAAIvAQACGBV4A1gAAdjLvMkb4zYE")
                except Exception as e:
                    logging.error(f"Offshift message failed for {user_id}: {e}")

    except Exception as e:
        logging.error(f"Error in send_off_shift: {e}")


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
    # Get all products below their threshold
    low_stock_products = await database.fetch_all("""
        SELECT name, quantity, unit FROM products
        WHERE quantity <= threshold AND threshold > 0
    """)

    # Get all admin user IDs
    admins = await database.fetch_all("SELECT admin_user_id FROM admins")

    if not low_stock_products or not admins:
        return  # No need to notify

    reminder_msg = "⚠️ *Low Stock Alert:*\nThe following products are running low:\n\n"
    for product in low_stock_products:
        quantity = product["quantity"]
        quantity_display = int(quantity) if quantity == int(quantity) else quantity
        reminder_msg += f"• {product['name']}: {quantity_display} {product['unit']}\n"

    for admin in admins:
        admin_id = admin["admin_user_id"]
        await bot.send_message(admin_id, reminder_msg, parse_mode="Markdown")





# ---------- DB SETUP ----------



load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

database = Database(DATABASE_URL)

async def init_db():
    try:
        await database.connect()

        # USERS table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                station TEXT,
                name TEXT,
                hourly_rate REAL
            )
        """)

        # WORK LOGS table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS work_logs (
                user_id BIGINT,
                station_name TEXT,
                date DATE,
                start_time TIME,
                end_time TIME,
                hours REAL,
                shift TEXT,
                PRIMARY KEY (user_id, date),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # ADMINS table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                admin_user_id BIGINT PRIMARY KEY,
                name TEXT
            )
        """)

        # Insert admin if not exists (UPSERT)
        await database.execute("""
            INSERT INTO admins (admin_user_id, name) VALUES (1291587607, 'Miostral')
            ON CONFLICT (admin_user_id) DO NOTHING
        """)

        # STATIONS table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS stations (
                station_id SERIAL PRIMARY KEY,
                name TEXT UNIQUE,
                hourly_rate REAL
            )
        """)

        # Insert stations if not exists
        stations = [
            ('bar', 350),
            ('tiramisu', 700),
            ('kitchen', 600),
            ('manager', 500)
        ]
        for name, rate in stations:
            await database.execute("""
                INSERT INTO stations (name, hourly_rate) VALUES (:name, :rate)
                ON CONFLICT (name) DO NOTHING
            """, values={"name": name, "rate": rate})

        # CATEGORIES table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id SERIAL PRIMARY KEY,
                name TEXT UNIQUE
            )
        """)

        # PRODUCTS table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id SERIAL PRIMARY KEY,
                name TEXT,
                quantity REAL,
                unit TEXT,
                category_id INTEGER REFERENCES categories(category_id),
                threshold REAL DEFAULT 0
            )
        """)

        # STATION_PRODUCTS table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS station_products (
                station_id INTEGER REFERENCES stations(station_id),
                product_id INTEGER REFERENCES products(product_id),
                PRIMARY KEY (station_id, product_id)
            )
        """)

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
    finally:
        await database.disconnect()


# ---------- BOT COMMANDS ----------




# ---------- REGISTER ----------
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_station = State()

@dp.message(Command("register"))
async def set_station(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    station = message.text.lower()

    if station not in ['bar', 'tiramisu', 'kitchen', 'manager']:
        await message.answer("⚠️ Invalid station. Please select one of: 'bar', 'tiramisu', 'kitchen', or 'manager'.")
        return

    query_hourly_rate = "SELECT hourly_rate FROM stations WHERE name = :station"
    row = await database.fetch_one(query=query_hourly_rate, values={"station": station})
    if not row:
        await message.answer("⚠️ Station not found. Please try again.")
        return
    hourly_rate = row["hourly_rate"]

    data = await state.get_data()
    name = data["name"]

    query_insert = """
        INSERT INTO users (user_id, name, station, hourly_rate)
        VALUES (:user_id, :name, :station, :hourly_rate)
        ON CONFLICT (user_id) DO UPDATE SET
            name = EXCLUDED.name,
            station = EXCLUDED.station,
            hourly_rate = EXCLUDED.hourly_rate
    """
    await database.execute(query=query_insert, values={
        "user_id": user_id,
        "name": name,
        "station": station,
        "hourly_rate": hourly_rate
    })

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
        query = """
        INSERT INTO admins (admin_user_id, name)
        VALUES (:user_id, :admin_name)
        ON CONFLICT (admin_user_id) DO NOTHING
        """
        await database.execute(query=query, values={"user_id": user_id, "admin_name": admin_name})

        await message.answer(f"✅ {admin_name}, you are now registered as an admin.")
    else:
        await message.answer("❌ Incorrect code. Access denied.")
    await state.clear()





# ---------- CHANGE STATION ----------

class ChangeStationStates(StatesGroup):
    waiting_for_new_station = State()

@dp.message(Command("change_station"))
async def change_station_start(message: Message, state: FSMContext):
    await message.answer("Please select a new station: 'bar', 'tiramisu', 'kitchen', or 'manager'.")
    await state.set_state(ChangeStationStates.waiting_for_new_station)

@dp.message(StateFilter(ChangeStationStates.waiting_for_new_station))
async def set_new_station(message: Message, state: FSMContext):
    new_station = message.text.lower()
    if new_station not in ['bar', 'tiramisu', 'kitchen', 'manager']:
        await message.answer("⚠️ Invalid station. Please select one of: 'bar', 'tiramisu', 'kitchen', or 'manager'.")
        return

    query_rate = "SELECT hourly_rate FROM stations WHERE name = :station"
    row = await database.fetch_one(query=query_rate, values={"station": new_station})

    if not row:
        await message.answer("Station not found in database.")
        await state.clear()
        return

    hourly_rate = row["hourly_rate"]
    user_id = str(message.from_user.id)

    query_update = """
    UPDATE users SET station = :station, hourly_rate = :hourly_rate WHERE user_id = :user_id
    """
    await database.execute(query=query_update, values={"station": new_station, "hourly_rate": hourly_rate, "user_id": user_id})

    await message.answer(f"✅ Your station has been updated to {new_station} with an hourly rate of {hourly_rate}.")
    await state.clear()

async def is_admin(user_id: str) -> bool:
    query = "SELECT 1 FROM admins WHERE admin_user_id = :user_id"
    row = await database.fetch_one(query=query, values={"user_id": user_id})
    return row is not None



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
    query = "INSERT INTO categories (name) VALUES (:name) ON CONFLICT DO NOTHING"
    await database.execute(query=query, values={"name": category_name})

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

    # Get or create category_id
    category_row = await database.fetch_one("SELECT category_id FROM categories WHERE name = :name", {"name": category_name})
    if category_row:
        category_id = category_row["category_id"]
    else:
        category_id = await database.execute("INSERT INTO categories (name) VALUES (:name) RETURNING category_id", {"name": category_name})

    await database.execute(
        """
        INSERT INTO products (name, quantity, unit, category_id)
        VALUES (:name, :quantity, :unit, :category_id)
        """,
        {"name": name, "quantity": quantity, "unit": unit, "category_id": category_id}
    )

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

    product = await database.fetch_one("SELECT quantity, unit FROM products WHERE product_id = :product_id", {"product_id": product_id})
    if not product:
        await message.answer("❌ Product not found.")
        return

    current_quantity = product["quantity"]
    unit = product["unit"]

    if quantity_used > current_quantity:
        await message.answer(f"❌ Insufficient stock. Only {current_quantity} {unit} available.")
        return

    new_quantity = current_quantity - quantity_used
    await database.execute(
        "UPDATE products SET quantity = :new_quantity WHERE product_id = :product_id",
        {"new_quantity": new_quantity, "product_id": product_id}
    )

    await message.answer(f"✅ Used {quantity_used} {unit} of product {product_id}. Remaining: {new_quantity} {unit}.")

# --- LIST PRODUCTS ---
@dp.message(Command("list_products"))
async def list_products(message: Message):
    user_id = str(message.from_user.id)
    if not await is_admin(user_id):
        await message.answer("❌ You don't have permission to use this command.")
        return

    rows = await database.fetch_all(
        """
        SELECT c.name as category_name, p.name as product_name, p.quantity, p.unit
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        ORDER BY c.name
        """
    )

    if not rows:
        await message.answer("❌ No products found.")
        return

    categories = {}
    for row in rows:
        cat = row["category_name"] or "Uncategorized"
        quantity = row["quantity"]
        # Format quantity as int if whole number, else float
        qty_display = int(quantity) if quantity == int(quantity) else quantity
        categories.setdefault(cat, []).append(f"{row['product_name']}: {qty_display} {row['unit']}")

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

    rows = await database.fetch_all(
        """
        SELECT p.name, p.quantity, p.unit FROM products p
        JOIN station_products sp ON p.product_id = sp.product_id
        WHERE sp.station_id = :station_id
        """,
        {"station_id": station_id}
    )

    if not rows:
        await message.answer(f"❌ No products found for station {station_id}.")
        return

    lines = [f"📦 Products at Station {station_id}:"]
    for row in rows:
        lines.append(f"{row['name']}: {row['quantity']} {row['unit']}")

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


@dp.callback_query(F.data.startswith("shift_"))
async def handle_shift_selection(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    shift = callback_query.data.replace("shift_", "")
    today = datetime.now().strftime("%d/%m/%Y")

    await database.execute("""
        INSERT INTO work_logs (user_id, date, shift)
        VALUES (:user_id, :date, :shift)
        ON CONFLICT (user_id, date) DO UPDATE SET shift = EXCLUDED.shift
    """, values={"user_id": user_id, "date": today, "shift": shift})

    shift_names = {
        "first": "First Shift (08:00–16:00)",
        "middle": "Middle Shift (12:00–20:00)",
        "second": "Second Shift (16:00–00:00)",
        "full": "Full Shift (08:00–00:00)",
        "off": "Off Today"
    }

    await callback_query.answer(f"✅ Shift set to: {shift_names.get(shift, shift.capitalize())}")


async def bot_send_shift_question():
    users = await database.fetch_all("SELECT user_id FROM users")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕗 First Shift (08:00–16:00)", callback_data="shift_first")],
            [InlineKeyboardButton(text="🌆 Middle Shift (12:00–20:00)", callback_data="shift_middle")],
            [InlineKeyboardButton(text="🌃 Second Shift (16:00–00:00)", callback_data="shift_second")],
            [InlineKeyboardButton(text="💟 Full Shift (08:00–00:00)", callback_data="shift_full")],
            [InlineKeyboardButton(text="❌ Off Today", callback_data="shift_off")],
        ]
    )

    for user in users:
        user_id = user["user_id"]
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

    is_admin = await database.fetch_one(
        "SELECT 1 FROM admins WHERE admin_user_id = :user_id",
        values={"user_id": user_id}
    )

    if not is_admin:
        await message.answer("❌ You don't have permission to use this command.")
        return

    low_stock_products = await database.fetch_all("""
        SELECT DISTINCT p.name, p.quantity, p.unit
        FROM products p
        JOIN station_products sp ON p.product_id = sp.product_id
        WHERE p.quantity <= :threshold
    """, values={"threshold": LOW_STOCK_THRESHOLD})

    if len(low_stock_products) >= MIN_LOW_STOCK_PRODUCTS:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        report_lines = [f"⚠️ Low Stock Products Report - {now_str}"]

        for product in low_stock_products:
            quantity = product["quantity"]
            quantity_display = int(quantity) if quantity == int(quantity) else quantity
            report_lines.append(f"{product['name']}: {quantity_display} {product['unit']}")

        report_lines.append(f"\nTotal Low Stock Products: {len(low_stock_products)}")
        await message.answer("\n".join(report_lines))
    else:
        await message.answer("🔔 Reminder: Low stock detected but fewer than 2 products. Please check inventory carefully.")


async def register_user(user_id: str):
    try:
        await database.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT
            )
        """)
        await database.execute("""
            INSERT INTO users (user_id) VALUES (:user_id)
            ON CONFLICT DO NOTHING
        """, values={"user_id": user_id})
    except Exception as e:
        print(f"Error registering user {user_id}: {e}")
        raise


@dp.message(Command("start_work"))
async def start_work(message: Message):
    try:
        user_id = str(message.from_user.id)
        await register_user(user_id)

        today = datetime.now().strftime("%d/%m/%Y")
        now = datetime.now().strftime("%H:%M")

        await database.execute("""
            CREATE TABLE IF NOT EXISTS work_logs (
                user_id TEXT,
                date TEXT,
                start_time TEXT,
                end_time TEXT,
                hours REAL,
                PRIMARY KEY (user_id, date)
            )
        """)

        await database.execute("""
            INSERT INTO work_logs (user_id, date, start_time, end_time, hours)
            VALUES (:user_id, :date, :start_time, '', 0)
            ON CONFLICT (user_id, date) DO UPDATE SET start_time = EXCLUDED.start_time
        """, values={"user_id": user_id, "date": today, "start_time": now})

        await message.answer(f"🟢 Work started at {now} on {today}")
        await message.answer("vay araa eli gorc")

        try:
            await message.answer_sticker("CAACAgIAAxkBAAIGjmgX2XtiKGwc5UQTnEeLuY8-4C7IAAKsFAACAVTJSxbQNn7AYn0fNgQ")
        except Exception as e:
            print(f"Failed to send sticker: {e}")

    except Exception as e:
        print(f"Error in /start_work command: {e}")
        await message.answer("❌ Something went wrong. Please try again later.")


@dp.message(Command("end_work"))
async def end_work(message: Message):
    user_id = str(message.from_user.id)
    now_time = datetime.now().strftime("%H:%M")

    row = await database.fetch_one("""
        SELECT date, start_time FROM work_logs
        WHERE user_id = :user_id AND (end_time IS NULL OR end_time = '')
        ORDER BY date DESC LIMIT 1
    """, values={"user_id": user_id})

    if not row:
        await message.answer("⚠️ You must start work first using /start_work")
        return

    work_date, start_time_str = row["date"], row["start_time"]
    start_time = datetime.strptime(start_time_str, "%H:%M")
    end_time = datetime.strptime(now_time, "%H:%M")

    # Handle overnight shift
    if end_time < start_time:
        end_time += timedelta(days=1)

    hours = round((end_time - start_time).seconds / 3600, 2)

    await database.execute("""
        UPDATE work_logs
        SET end_time = :end_time, hours = :hours
        WHERE user_id = :user_id AND date = :date
    """, values={"end_time": now_time, "hours": hours, "user_id": user_id, "date": work_date})

    await message.answer(f"🔴 Work ended at {now_time}. Total worked: {hours} hours")

    try:
        await message.answer_sticker("CAACAgIAAxkBAAIGkGgX2aYJIzvH4fKF3hj0OpWnWw4RAALrFwACOFvQS2ytXSeKU4UdNgQ")
    except Exception as e:
        print(f"Failed to send sticker: {e}")


@dp.message(Command("report"))
async def report(message: Message):
    user_id = str(message.from_user.id)
    rows = await database.fetch_all("""
        SELECT date, start_time, end_time, hours
        FROM work_logs
        WHERE user_id = :user_id
        ORDER BY date
    """, values={"user_id": user_id})

    if not rows:
        await message.answer("❌ No data available.")
        return

    total = sum(row["hours"] or 0 for row in rows)
    lines = ["🗓️ Work Report:"]
    for row in rows:
        lines.append(f"{row['date']} | Start: {row['start_time']} | End: {row['end_time']} | Hours: {row['hours']}")
    lines.append(f"\n🧮 Total hours: {total}")

    await message.answer("\n".join(lines), parse_mode="Markdown")

    try:
        await message.answer_sticker("CAACAgIAAxkBAAIGjGgX2RIsRENWszvV4FcPXd9KUBR1AAI-FQAC4TvISyGu9Oi89CQPNgQ") 
    except Exception as e:
        print(f"Failed to send sticker: {e}")



# ---------- EXCEL ----------
@router.message(Command("export_excel"))
async def export_excel(message: Message):
    user_id = str(message.from_user.id)
    try:
        logs = await database.fetch_all(
            "SELECT date, start_time, end_time, hours FROM work_logs WHERE user_id = :user_id ORDER BY date",
            values={"user_id": user_id}
        )
        if not logs:
            await message.answer("❌ No work log data found.")
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Work Logs"

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
            ws.append([row["date"], row["start_time"], row["end_time"], row["hours"]])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        file = BufferedInputFile(output.read(), filename=f"report_{user_id}.xlsx")
        await message.answer_document(file, caption="📊 Your work log report.")

    except Exception as e:
        await message.answer("❌ Failed to export your work log.")
        print(f"[Export Error]: {e}")


async def send_monthly_summary():
    current_month = datetime.now().strftime("%m")
    current_year = datetime.now().strftime("%Y")

    users = await database.fetch_all("SELECT user_id FROM users")
    for user in users:
        user_id = user["user_id"]
        row = await database.fetch_one(
            """
            SELECT SUM(hours) AS total_hours FROM work_logs
            WHERE user_id = :user_id AND to_char(to_date(date, 'DD/MM/YYYY'), 'MM') = :month
            AND to_char(to_date(date, 'DD/MM/YYYY'), 'YYYY') = :year
            """,
            values={"user_id": user_id, "month": current_month, "year": current_year}
        )
        total_hours = row["total_hours"] or 0.0

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

    await database.execute(
        """
        INSERT INTO work_logs (user_id, date, start_time, end_time, hours)
        VALUES (:user_id, :date, 'OFF', 'OFF', 0.0)
        ON CONFLICT (user_id, date) DO UPDATE SET start_time='OFF', end_time='OFF', hours=0.0
        """,
        values={"user_id": user_id, "date": off_date}
    )

    await message.answer(f"✅ Marked {off_date} as an OFF day 🛌", parse_mode="Markdown")
    try:
        await message.answer_sticker("CAACAgIAAxkBAAIGlmgX2gpRBCe99llBp1SDW4D6Jhj_AALAFgAC-FLQS9CqJ2GwUsWCNgQ")
    except Exception as e:
        print(f"Failed to send sticker: {e}")


@dp.message(Command("edit"))
async def edit_work_time(message: Message):
    user_id = str(message.from_user.id)
    args = message.text.strip().split()

    if len(args) != 4:
        await message.answer("⚠️ Usage: `/edit dd/mm/yyyy HH:MM HH:MM`", parse_mode="Markdown")
        return

    date_str, start_str, end_str = args[1], args[2], args[3]

    try:
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

    if end_time < start_time:
        end_time += timedelta(days=1)

    work_seconds = (end_time - start_time).total_seconds()
    work_hours = round(work_seconds / 3600, 2)

    await database.execute(
        """
        INSERT INTO work_logs (user_id, date, start_time, end_time, hours)
        VALUES (:user_id, :date, :start_time, :end_time, :hours)
        ON CONFLICT (user_id, date) DO UPDATE
        SET start_time = EXCLUDED.start_time, end_time = EXCLUDED.end_time, hours = EXCLUDED.hours
        """,
        values={"user_id": user_id, "date": date_str, "start_time": start_str, "end_time": end_str, "hours": work_hours}
    )

    await message.answer(
        f"✏️ Updated `{date_str}`:\n🕒 Start: `{start_str}`\n🕔 End: `{end_str}`\n📊 Total: *{work_hours} hours*",
        parse_mode="Markdown"
    )


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

    await database.execute(
        "DELETE FROM work_logs WHERE user_id = :user_id AND date = :date",
        values={"user_id": user_id, "date": date_str}
    )

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
    await database.execute(
        "DELETE FROM work_logs WHERE user_id = :user_id",
        values={"user_id": user_id}
    )
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
    user_row = await database.fetch_one(
        "SELECT station, hourly_rate FROM users WHERE user_id = :user_id",
        values={"user_id": user_id}
    )
    if not user_row:
        await message.answer("❌ You must register first using /register.")
        return

    station = user_row["station"]
    hourly_rate = user_row["hourly_rate"]

    total_hours_row = await database.fetch_one(
        "SELECT SUM(hours) AS total_hours FROM work_logs WHERE user_id = :user_id",
        values={"user_id": user_id}
    )
    total_hours = total_hours_row["total_hours"] or 0.0

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
    await bot.delete_webhook(drop_pending_updates=True)
    scheduler.start()
    dp.include_router(router)
    await dp.start_polling(bot)



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
