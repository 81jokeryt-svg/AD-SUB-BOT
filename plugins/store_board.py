# Don't Remove Credit Tg - @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
from pyrogram import Client, filters, enums
from pyrogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardRemove
)
from plugins.dbusers import db

# User states pagination track karne ke liye
USER_STORE_STATES = {}

# ─── 1. BOTTOM KEYBOARD CATEGORIES MENU (CONNECTED WITH START.PY) ───
def get_platform_markup():
    """Start.py se coordinate karne ke liye main categories filter selection grid"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("Pratilipi FM"), KeyboardButton("Pocket FM")],
            [KeyboardButton("Other")],
            [KeyboardButton("« Back to Menu")]
        ],
        resize_keyboard=True
    )

def get_categories_markup():
    """Fallback validation name handling"""
    return get_platform_markup()


# ─── 2. PAGINATED ITEMS MENU ENGINE (PRATILIPI + POCKET + COMBO) ───
async def get_store_pagination_markup(category_type, page=1):
    """Asynchronously matches database fields and slices items (8 items per page)"""
    limit = 8
    skip = (page - 1) * limit
    
    if category_type == "pratilipi":
        query = {"story_name": {"$exists": True}, "source": "pratilipi", "is_combo": {"$exists": False}}
    elif category_type == "pocket":
        query = {"story_name": {"$exists": True}, "source": "pocket", "is_combo": {"$exists": False}}
    elif category_type == "combo":
        query = {"is_combo": True}
    else:
        query = {}
        
    total_items = await db.count_stories_by_filter(query)
    
    if total_items == 0:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton("🚫 STORE IS EMPTY")],
                [KeyboardButton("🔙 BACK TO CATEGORIES")]
            ], 
            resize_keyboard=True
        )

    sliced_items = await db.get_stories_by_filter(query, skip, limit)
    keyboard_buttons = []

    # Display Loop with First Line Title Rule integration
    for index, item in enumerate(sliced_items, start=skip + 1):
        if category_type == "combo":
            btn_text = f"🎁 {index}. {item.get('combo_name', 'Unnamed Combo')} ➔ [ ₹{item['price']} ]"
            keyboard_buttons.append([KeyboardButton(btn_text)])
        else:
            raw_title = item.get('story_name') or item.get('name') or 'Unnamed Story'
            # Title Split Logic: Sirf pehli line ko title banata hai
            clean_title = raw_title.split("\n")[0].strip()
            btn_text = f"{index}. {clean_title} [ ₹{item.get('price', '49')} ]"
            keyboard_buttons.append([KeyboardButton(btn_text)])
            
    # Navigation Buttons Setup
    nav_buttons = []
    if page > 1:
        nav_buttons.append(KeyboardButton("‹ PREV"))
    if (skip + limit) < total_items:
        nav_buttons.append(KeyboardButton("NEXT ›"))
        
    if nav_buttons:
        keyboard_buttons.append(nav_buttons)
        
    # Essential Standard Controls
    keyboard_buttons.append([KeyboardButton("🔙 BACK TO CATEGORIES"), KeyboardButton("❌ CLOSE STORE")])
    return ReplyKeyboardMarkup(keyboard_buttons, resize_keyboard=True)


# ─── 3. TEXT MESSAGE ASYNC CENTRAL ROUTER ───
@Client.on_message(filters.text & filters.private & filters.incoming, group=1)
async def store_board_central_router(client, message):
    user_id = message.from_user.id
    text = message.text

    # Keywords strictly matched to new buttons
    allowed_keywords = ["Pratilipi FM", "Pocket FM", "Other", "🔙 BACK TO CATEGORIES", "« Back to Menu", "❌ CLOSE STORE", "🚫 STORE IS EMPTY"]
    is_navigation = text in ["NEXT ›", "‹ PREV"]
    is_item_selection = any(char in text for char in ['[ ₹', '➔ [', '[₹'])

    if text not in allowed_keywords and not is_navigation and not is_item_selection:
        return 

    if text in ["« Back to Menu", "❌ CLOSE STORE"]:
        USER_STORE_STATES[user_id] = {"category": "home", "page": 1}
        return await message.reply_text(
            "<b>Returning to Main Menu Dashboard...</b>", 
            reply_markup=ReplyKeyboardRemove()
        )

    if text == "🔙 BACK TO CATEGORIES":
        USER_STORE_STATES[user_id] = {"category": "home", "page": 1}
        return await message.reply_text(
            "🎧 <b>Platform Selection</b>\n\nChoose a platform from the keyboard below:", 
            reply_markup=get_platform_markup()
        )

    # State Categories router map
    category_map = {
        "Pratilipi FM": ("pratilipi", "✨ <b>ᴘʀᴀᴛɪʟɪᴘɪ ғᴍ sᴛᴏʀɪᴇs</b>"),
        "Pocket FM": ("pocket", "🎧 <b>ᴘᴏᴄᴋᴇᴛ ғᴍ sᴛᴏʀɪᴇs</b>"),
        "Other": ("combo", "🎁 <b>✨ ᴘʀᴇᴍɪᴜᴍ ᴄᴏᴍʙᴏ ᴘᴀᴄᴋs ✨</b>")
    }

    if text in category_map:
        cat_key, cat_header = category_map[text]
        USER_STORE_STATES[user_id] = {"category": cat_key, "page": 1}
        
        caption_text = f"{cat_header}\n\nAll available stories and their prices are shown in the menu below. Please tap on any story name from the keyboard menu."
        markup_keyboard = await get_store_pagination_markup(cat_key, page=1)
        return await message.reply_text(caption_text, reply_markup=markup_keyboard)

    # Multi-page Switches Execution
    if is_navigation:
        state = USER_STORE_STATES.get(user_id, {"category": "home", "page": 1})
        if state["category"] == "home":
            return
            
        state["page"] += 1 if text == "NEXT ›" else -1
        USER_STORE_STATES[user_id] = state
        
        markup_keyboard = await get_store_pagination_markup(state["category"], page=state["page"])
        return await message.reply_text(
            f"<b>✨ Page {state['page']} Packages:</b>", 
            reply_markup=markup_keyboard
        )

    # Item Selection Processing Block (Hides reply keyboard layout)
    if is_item_selection:
        clean_name = text
        try:
            if "." in text:
                clean_name = text.split(".", 1)[1].split("[")[0].strip()
            else:
                clean_name = text.split("[")[0].strip()
            if "🎁" in text:
                clean_name = text.replace("🎁", "").split("➔")[0].strip()
        except Exception:
            pass

        state = USER_STORE_STATES.get(user_id, {"category": "pocket"})
        
        # Async Single document lookup based on active configuration
        if state["category"] == "combo":
            data = await db.find_single_story({"combo_name": {"$regex": f"^{re.escape(clean_name)}", "$options": "i"}})
        else:
            # FIXED LOOKUP: $regex match strict start, ignoring trail spaces/case sensitive issues
            data = await db.find_single_story({
                "$or": [
                    {"story_name": {"$regex": f"^{re.escape(clean_name)}", "$options": "i"}},
                    {"name": {"$regex": f"^{re.escape(clean_name)}", "$options": "i"}}
                ],
                "source": state["category"]
            })

        if not data:
            # Alternate fallback logic if strict start fails
            if state["category"] == "combo":
                data = await db.find_single_story({"combo_name": {"$regex": re.escape(clean_name), "$options": "i"}})
            else:
                data = await db.find_single_story({
                    "$or": [
                        {"story_name": {"$regex": re.escape(clean_name), "$options": "i"}},
                        {"name": {"$regex": re.escape(clean_name), "$options": "i"}}
                    ],
                    "source": state["category"]
                })
                
            if not data:
                return await message.reply_text("❌ <i>Story Details nahi mil saki. Kripya list se sahi select karein.</i>")

        #Visual cleanup alert
        loading_alert = await message.reply_text(
            "⏳ <i>Loading Story Details...</i>", 
            reply_markup=ReplyKeyboardRemove(), 
            parse_mode=enums.ParseMode.HTML
        )

        inline_markup = []
        db_id = str(data.get('item_id') or data.get('channel_id') or data.get('_id'))

        if data.get('is_combo'):
            inline_markup.append([InlineKeyboardButton(f"✅ CONFIRM & PAY COMBO - ₹{data['price']}", callback_data=f"pay_{db_id}")])
            header = "🎁 <b>ᴘʀᴇᴍɪᴜᴍ sᴘᴇᴄɪᴀʟ ᴄᴏᴍʙᴏ ʙᴜɴᴅʟᴇ</b>"
            item_label = data.get('combo_name')
            desc_text = f"📝 <b>ɪɴᴄʟᴜᴅᴇᴅ sᴛᴏʀɪᴇs:</b>\n<i>{data.get('description', 'All premium files included.')}</i>"
        else:
            inline_markup.append([InlineKeyboardButton(f"🔓 UNLOCK PREMIUM STORY - ₹{data.get('price', '12')}", callback_data=f"pay_{db_id}")])
            header = f"🔥 <b><b>ᴘʀᴇᴍɪᴜᴍ ᴇxᴄʟᴜsɪᴠᴇ sᴛᴏʀʏ</b> ({data.get('source', 'audio').upper()})</b>"
            
            raw_lbl = data.get('story_name') or data.get('name') or 'Premium Story'
            item_label = raw_lbl.split("\n")[0].strip() # First line split check
            desc_text = "🤖 <b>ᴅᴇʟɪᴠᴇʀỹ:</b> <code><b>ɪɴsᴛᴀɴᴛ ʙᴏᴛ ʟɪɴᴋ ᴀᴄᴄᴇss</b></code>"

        if data.get('demo_link'):
            inline_markup.append([InlineKeyboardButton("📺 ᴠɪᴇᴡ ǫᴜᴀʟɪᴛʏ ᴅᴇᴍᴏ", url=data['demo_link'])])
            
        inline_markup.append([InlineKeyboardButton("⬅️ BACK TO LIST", callback_data="back_to_store_list")])

        details_layout = f"{header}\n──────────────────────────\n📦 <b><u>ɪᴛᴇᴍ:</u></b> <code>{item_label}</code>\n💰 <b><u>ᴘʀɪᴄᴇ:</u></b> <b>₹{data.get('price', '12')}</b>\n\n{desc_text}\n──────────────────────────"
        photo_id = data.get('file_id')

        try:
            await loading_alert.delete()
        except:
            pass

        if photo_id:
            await client.send_photo(message.chat.id, photo=photo_id, caption=details_layout, reply_markup=InlineKeyboardMarkup(inline_markup))
        else:
            await client.send_message(message.chat.id, text=details_layout, reply_markup=InlineKeyboardMarkup(inline_markup))


# ─── 4. BACK TO LIST INLINE CALLBACK CONTROLLER ───
@Client.on_callback_query(filters.regex("^back_to_store_list$"))
async def process_return_store_callback(client, call):
    user_id = call.from_user.id
    await call.answer()
    
    # SMART DELETE: Cheks if active message contains photo structure before deletion
    try:
        # Cheks if message contains active media (photo map)
        if call.message.photo:
            # Pure standard photo structure must be deleted strictly on list returns
            await call.message.delete()
        else:
            # Standard text messages can be gracefully morphed safely
            await call.message.edit_text("👇 <i>List se select karein:</i>", reply_markup=None)
    except Exception:
        # Fallback if standard methods are rejected
        try: await call.message.delete()
        except: pass
        
    state = USER_STORE_STATES.get(user_id, {"category": "pocket", "page": 1})
    markup_keyboard = await get_store_pagination_markup(state["category"], page=state["page"])
    
    # Strictly send dynamic new message after old one is flushed
    await client.send_message(
        chat_id=call.message.chat.id, 
        text="👇 <i>Apni pasand ka item select karke full access lein:</i>", 
        reply_markup=markup_keyboard
    )


# ─── 5. FIXED: UNLOCK BUTTON PAY CALLBACK HANDLER (DELETE THEN SEND FLOW) ───
@Client.on_callback_query(filters.regex("^pay_"))
async def process_payment_gateway_routing(client, call):
    """Triggers strictly on intermediate confirm intermediate intermediates, applying delete-then-send layout"""
    await call.answer()
    story_id = call.data.split("_", 1)[1]
    
    # DB se accurate item details recover karein
    data = await db.find_single_story({
        "$or": [
            {"item_id": story_id},
            {"channel_id": story_id},
            {"_id": story_id}
        ]
    })
    
    if not data:
        data = await db.find_single_story({"combo_name": story_id})
        
    price = data.get('price', '12') if data else '12'
    title = data.get('combo_name') or (data.get('story_name') or data.get('name', 'Premium Item')).split("\n")[0].strip()

    # Buttons layout strictly lowercase
    payment_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 PAY VIA QR SCAN", callback_data=f"qr_{story_id}")],
        [InlineKeyboardButton("💳 PAY VIA UPI ID", callback_data=f"upi_{story_id}")],
        [InlineKeyboardButton("❌ CANCEL PAYMENT", callback_data="back_to_store_list")]
    ])
    
    payment_layout = (
        "⚙️ <b><u>ᴄᴏɴғɪʀᴍ sᴇʟᴇᴄᴛɪᴏɴ</u></b>\n"
        "──────────────────────────\n"
        f"📦 <b>ɪᴛᴇᴍ:</b> <code>{title}</code>\n"
        f"💰 <b>ᴀᴍᴏᴜɴᴛ:</b> <code>₹{price}</code>\n\n"
        "➔ <b>ᴘᴀỹᴍᴇɴᴛ ᴍᴇᴛʜᴏᴅ sᴇʟᴇᴄᴛ ᴋᴀʀᴇɪɴ:</b>\n"
        "──────────────────────────"
    )
    
    # CRITICAL CHANGE: The intermediate story details card must be strictly deleted before sending pay intermediate layout
    try:
        # Async Motor based document deletion reference check to flush photo safely
        await call.message.delete()
    except Exception as e:
        # Safe Side fallback for standard text edit
        try:
            await call.message.edit_reply_markup(reply_markup=None) # Clean intermediate state pointers safely
        except: pass

    # Strictly sends unified dynamic new pay intermediate checks block
    await client.send_message(
        chat_id=call.message.chat.id,
        text=payment_layout,
        reply_markup=payment_keyboard
    )
