import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)

# === CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # stored securely in Railway later
MEETING_ROOM_NAME = "The Batcave"

# === DATA STORAGE (in memory — simple for now) ===
bookings = {}  # { "2025-10-02": [("12:00", "14:00", "Sean")] }

# === STEP 1: START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🦇 Welcome to the Batcave Booking Bot!\n\n"
        f"Use /book to book the meeting room.\n"
        f"Use /availability to check available times.\n"
        f"Use /mybookings to see your current bookings."
    )

# === STEP 2: CHECK AVAILABILITY ===
async def availability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().date()
    msg = f"📅 Available slots for {MEETING_ROOM_NAME} (next 3 days):\n\n"

    for i in range(3):
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        booked_slots = bookings.get(date_str, [])
        booked_ranges = [f"{b[0]}-{b[1]}" for b in booked_slots]
        if booked_ranges:
            msg += f"🔹 {date_str}: BOOKED ({', '.join(booked_ranges)})\n"
        else:
            msg += f"✅ {date_str}: All slots available\n"

    await update.message.reply_text(msg)

# === STEP 3: BOOKING ===
async def book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().date()
    keyboard = [
        [InlineKeyboardButton((today + timedelta(days=i)).strftime("%Y-%m-%d"), callback_data=(today + timedelta(days=i)).strftime("%Y-%m-%d"))]
        for i in range(3)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📅 Choose a date to book:", reply_markup=reply_markup)

async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    date_str = query.data
    context.user_data["selected_date"] = date_str

    # Offer time slots
    times = [("09:00", "11:00"), ("11:00", "13:00"), ("13:00", "15:00"), ("15:00", "17:00")]
    keyboard = [[InlineKeyboardButton(f"{t[0]} - {t[1]}", callback_data=f"{t[0]}-{t[1]}")] for t in times]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(f"🕒 Select a time slot for {date_str}:", reply_markup=reply_markup)

async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    time_range = query.data
    start_time, end_time = time_range.split("-")
    date_str = context.user_data["selected_date"]
    username = query.from_user.first_name or query.from_user.username

    if date_str not in bookings:
        bookings[date_str] = []

    # Check if time already booked
    for b in bookings[date_str]:
        if b[0] == start_time and b[1] == end_time:
            await query.edit_message_text("❌ That time slot is already booked!")
            return

    # Save booking
    bookings[date_str].append((start_time, end_time, username))
    await query.edit_message_text(f"✅ Booked {MEETING_ROOM_NAME} on {date_str} from {start_time} to {end_time} for {username}!")

# === STEP 4: VIEW MY BOOKINGS ===
async def mybookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.first_name or update.message.from_user.username
    user_bookings = []

    for date, slots in bookings.items():
        for start, end, user in slots:
            if user == username:
                user_bookings.append(f"📅 {date} | 🕒 {start}-{end}")

    if user_bookings:
        await update.message.reply_text("🦇 Your bookings:\n" + "\n".join(user_bookings))
    else:
        await update.message.reply_text("You don’t have any bookings yet.")

# === MAIN APP ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("availability", availability))
    app.add_handler(CommandHandler("book", book))
    app.add_handler(CommandHandler("mybookings", mybookings))
    app.add_handler(CallbackQueryHandler(handle_date_selection, pattern=r"^\d{4}-\d{2}-\d{2}$"))
    app.add_handler(CallbackQueryHandler(handle_time_selection, pattern=r"^\d{2}:\d{2}-\d{2}:\d{2}$"))

    print("🤖 Bot is running... (press Ctrl+C to stop)")
    app.run_polling()

if __name__ == "__main__":
    main()
