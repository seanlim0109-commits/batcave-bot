import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# -------------------------------
# CONFIGURATION
# -------------------------------
GROUP_ID = 5094667500  # Your private Telegram group ID
ADMIN_USERNAMES = ["seeeeannnn"]  # Admin users

START_HOUR = 8   # Booking starts at 8am
END_HOUR = 18    # Booking ends at 6pm
SLOT_DURATION = 1  # 1 hour per slot
DATE_RANGE_DAYS = 365 * 10  # Allows booking for the next 10 years

# In-memory storage for bookings
# Format: { "YYYY-MM-DD": { "HH:MM": "username" } }
bookings = {}

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def get_available_slots(date: str):
    all_slots = [f"{h:02d}:00" for h in range(START_HOUR, END_HOUR)]
    booked_slots = bookings.get(date, {})
    return [slot for slot in all_slots if slot not in booked_slots]

def is_valid_date(date_str: str):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now().date()
        return date_obj.date() >= today
    except ValueError:
        return False

# -------------------------------
# COMMAND HANDLERS
# -------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    await update.message.reply_text(
        "🦇 Welcome to the Batcave booking bot!\n"
        "Use /book to select a date and time slot."
    )

# STEP 1: Show date selection
async def book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    keyboard = []
    today = datetime.now()
    for i in range(DATE_RANGE_DAYS):
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        keyboard.append([InlineKeyboardButton(date_str, callback_data=f"DATE|{date_str}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a date:", reply_markup=reply_markup)

# STEP 2: Handle date selection
async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    query = update.callback_query
    await query.answer()
    if not query.data.startswith("DATE|"):
        return

    date_str = query.data.split("|")[1]
    context.user_data["selected_date"] = date_str

    slots = get_available_slots(date_str)
    if not slots:
        await query.edit_message_text(f"❌ No available slots on {date_str}.")
        return

    keyboard = [[InlineKeyboardButton(slot, callback_data=f"SLOT|{slot}")] for slot in slots]
    await query.edit_message_text(f"Select a slot for {date_str}:", reply_markup=InlineKeyboardMarkup(keyboard))

# STEP 3: Handle timeslot selection
async def handle_slot_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    query = update.callback_query
    await query.answer()
    if not query.data.startswith("SLOT|"):
        return

    slot = query.data.split("|")[1]
    date_str = context.user_data.get("selected_date")
    if not date_str:
        await query.edit_message_text("❌ Error: Date not selected.")
        return

    if slot in bookings.get(date_str, {}):
        await query.edit_message_text(f"❌ {slot} on {date_str} is already booked.")
        return

    username = query.from_user.username or query.from_user.first_name
    if date_str not in bookings:
        bookings[date_str] = {}
    bookings[date_str][slot] = username

    await query.edit_message_text(f"✅ {username} booked {slot} on {date_str}.")

# -------------------------------
# ADMIN & USER BOOKING COMMANDS
# -------------------------------
async def all_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    username = update.message.from_user.username
    if username not in ADMIN_USERNAMES:
        await update.message.reply_text("❌ You are not authorized to see all bookings.")
        return

    msg = "🦇 All Batcave bookings:\n"
    for date, slots in sorted(bookings.items()):
        for slot, user in sorted(slots.items()):
            msg += f"{date} | {slot} | {user}\n"

    if not bookings:
        msg = "No bookings yet."
    await update.message.reply_text(msg)

async def my_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    username = update.message.from_user.username
    msg = "🦇 Your bookings:\n"
    found = False
    for date, slots in bookings.items():
        for slot, user in slots.items():
            if user == username:
                msg += f"{date} | {slot}\n"
                found = True
    if not found:
        msg = "You have no bookings yet."
    await update.message.reply_text(msg)

# -------------------------------
# MAIN BOT SETUP
# -------------------------------
def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("book", book))
    app.add_handler(CallbackQueryHandler(handle_date_selection, pattern="^DATE\\|"))
    app.add_handler(CallbackQueryHandler(handle_slot_selection, pattern="^SLOT\\|"))
    app.add_handler(CommandHandler("allbookings", all_bookings))
    app.add_handler(CommandHandler("mybookings", my_bookings))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
