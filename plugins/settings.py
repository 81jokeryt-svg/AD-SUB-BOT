from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
# Apne folder structure ke mutabiq utils se SETTINGS aur keyboard generator import karein
from utils import SETTINGS, generate_settings_keyboard 

# 1. SETTINGS COMMAND HANDLER 
# Isse user/admin ka premium settings menu open hoga
@Client.on_message(filters.command("settings") & filters.private)
async def open_settings(client, message):
    user_id = message.from_user.id
    
    # Premium Layout Caption
    text = (
        "╔════════════════════════╗\n"
        "🎬   **VENOM FILE STORE BOT**\n"
        "╚════════════════════════╝\n\n"
        "⚙️ **HERE IS THE SETTINGS MENU**\n"
        "Customize your settings as per your need."
    )
    
    # Keyboard call karke message bhej rahe hain
    await message.reply_text(
        text, 
        reply_markup=generate_settings_keyboard(user_id)
    )


# 2. DYNAMIC TOGGLE CALLBACK HANDLER
# Jab koi user ya admin button par click karega toh ye dynamic edit karega
@Client.on_callback_query(filters.regex(r"^toggle_"))
async def toggle_settings_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Callback data se action key nikalna (e.g., 'toggle_link_shortener' -> 'link_shortener')
    setting_key = callback_query.data.replace("toggle_", "")
    
    # Agar utils.py ki SETTINGS dict mein is user ka data nahi hai, toh initialize karein
    if user_id not in SETTINGS:
        # Default keys populate karne ke liye keyboard trigger call kar dete hain
        generate_settings_keyboard(user_id)
        
    # Purani value ko check karke invert (toggle) karna (True hai toh False, False hai toh True)
    old_value = SETTINGS[user_id].get(setting_key, False)
    SETTINGS[user_id][setting_key] = not old_value
    
    # User ko screen par short toast notification dikhane ke liye
    status_str = "ENABLED ✅" if SETTINGS[user_id][setting_key] else "DISABLED ❌"
    clean_name = setting_key.replace('_', ' ').title()
    await callback_query.answer(f"{clean_name} is now {status_str}", show_alert=False)
    
    # Bina screen flash ya naya message bheje, buttons ka markup live refresh karna
    await callback_query.message.edit_reply_markup(
        reply_markup=generate_settings_keyboard(user_id)
    )

