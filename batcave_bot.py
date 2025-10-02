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
        "Use /book <YYYY-MM-DD> to book a 1-hour slot."
    )

async def book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: /book YYYY-MM-DD")
        return

    date_str = context.args[0]
    if not is_valid_date(date_str):
        await update.message.reply_text("❌ Invalid date. Please use YYYY-MM-DD for today or future dates.")
        return

    available_slots = get_available_slots(date_str)
    if not available_slots:
        await update.message.reply_text(f"❌ No available slots on {date_str}.")
        return

    keyboard = [[InlineKeyboardButton(slot, callback_data=f"{date_str}|{slot}")] for slot in available_slots]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Select a slot on {date_str}:", reply_markup=reply_markup)

async def slot_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    query = update.callback_query
    await query.answer()
    date_str, slot = query.data.split("|")

    if slot in bookings.get(date_str, {}):
        await query.edit_message_text(f"❌ Sorry, {slot} on {date_str} is already booked.")
        return

    if date_str not in bookings:
        bookings[date_str] = {}
    username = query.from_user.username or query.from_user.first_name
    bookings[date_str][slot] = username

    await query.edit_message_text(f"✅ {username} booked {slot} on {date_str}.")

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
    app.add_handler(CallbackQueryHandler(slot_selection))
    app.add_handler(CommandHandler("allbookings", all_bookings))
    app.add_handler(CommandHandler("mybookings", my_bookings))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
