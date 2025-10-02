from datetime import datetime, timedelta

# STEP 1: Show next 30 days as buttons
async def book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    keyboard = []
    today = datetime.now()
    for i in range(30):
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        keyboard.append([InlineKeyboardButton(date_str, callback_data=f"DATE|{date_str}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a date:", reply_markup=reply_markup)

# STEP 2: Handle date selection and show timeslots
async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("DATE|"):
        return
    date_str = query.data.split("|")[1]
    context.user_data["selected_date"] = date_str

    slots = get_available_slots(date_str)  # your existing function
    keyboard = [[InlineKeyboardButton(slot, callback_data=f"SLOT|{slot}")] for slot in slots]
    await query.edit_message_text(f"Select a slot for {date_str}:", reply_markup=InlineKeyboardMarkup(keyboard))

# STEP 3: Handle timeslot selection
async def handle_slot_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
