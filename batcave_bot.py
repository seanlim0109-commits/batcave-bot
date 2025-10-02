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

START_HOUR = 8   # 8am
END_HOUR = 18    # 6pm
SLOT_DURATION = 1  # 1 hour per slot
DATE_PAGE_SIZE = 7  # Show 7 days per page for pagination

# In-memory storage
bookings = {}  # { "YYYY-MM-DD": { "HH:MM": "username" } }

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def get_available_slots(date_str):
    """Return all available 1-hour slots for a given date."""
    all_slots = [f"{h:02d}:00" for h in range(START_HOUR, END_HOUR)]
    booked_slots = bookings.get(date_str, {})
    return [slot for slot in all_slots if slot not in booked_slots]

def generate_date_keyboard(start_date, page_size=DATE_PAGE_SIZE):
    """Generate inline keyboard with a page of dates."""
    keyboard = []
    for i in range(page_size):
        date = start_date + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        keyboard.append([InlineKeyboardButton(date_str, callback_data=f"DATE|{date_str}")])
    # Add next page button
    next_page_date = start_date + timedelta(days=page_size)
    keyboard.append([InlineKeyboardButton("Next ➡️", callback_data=f"PAGE|{next_page_date.strftime('%Y-%m-%d')}")])
    return InlineKeyboardMarkup(keyboard)

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

# /book command
async def book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    today = datetime.now()
    keyboard = generate_date_keyboard(today)
    await update.message.reply_text("Select a date:", reply_markup=keyboard)

# Handle date button selection
async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    query = update.callback_query
    await query.answer()

    if query.data.startswith("PAGE|"):
        next_start_str = query.data.split("|")[1]
        next_start = datetime.strptime(next_start_str, "%Y-%m-%d")
        keyboard = generate_date_keyboard(next_start)
        await query.edit_message_text("Select a date:", reply_markup=keyboard)
        return

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

# Handle timeslot button selection
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
# ADMIN & USER COMMANDS
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
    app.add_handler(CallbackQueryHandler(handle_date_selection, pattern="^PAGE\\|"))
    app.add_handler(CallbackQueryHandler(handle_slot_selection, pattern="^SLOT\\|"))
    app.add_handler(CommandHandler("allbookings", all_bookings))
    app.add_handler(CommandHandler("mybookings", my_bookings))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
