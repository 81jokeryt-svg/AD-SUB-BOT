# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import uuid
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.dbusers import db  # Aapki database file se db instance
import config

# Admin state handling pipelines track karne ke liye dict
ADMIN_STORY_STATES = {}

# --- 1. ADMIN COMMAND INITIATOR ---
@Client.on_message(filters.command("add_story") & filters.private & filters.incoming)
async def start_add_story(client, message):
    if message.from_user.id != config.ADMIN_ID: 
        return
    
    # Fresh initialization
    ADMIN_STORY_STATES[message.from_user.id] = {"step": "get_name"}
    
    await message.reply_text(
        "🎬 <b>sᴛᴏʀʏ sᴇᴛᴜᴘ:</b>\n\n"
        "Story ka naam kya hai?\n"
        "<i>(Aap direct <b>Photo</b> bhi bhej sakte hain, bas uske <b>Caption</b> mein Story ka naam likh dein)</i>\n\n"
        "➔ Setup rokne ke liye <code>/cancel</code> likhein.", 
        parse_mode=enums.ParseMode.HTML
    )


# --- 2. CONVERSATION STEPS FLOW CONTROLLER ---
@Client.on_message(filters.private & filters.incoming, group=3)
async def story_setup_conversation_router(client, message):
    user_id = message.from_user.id
    state = ADMIN_STORY_STATES.get(user_id)
    
    if not state:
        return  # Regular users ko ignore karega

    # CRITICAL FIX: Agar koi command bhejta hai, toh use step inputs ke sath mix nahi karna hai
    if message.text and message.text.strip().startswith("/"):
        if message.text.strip() == "/cancel":
            ADMIN_STORY_STATES.pop(user_id, None)
            return await message.reply_text("❌ Setup cancelled.")
        return # Baaki commands (jaise /add_story khud) ko skip karega taaki automatic double execution na ho

    current_step = state.get("step")

    # STEP A: NAME & MEDIA EXTRACTION
    if current_step == "get_name":
        story_name = None
        file_id = None

        if message.photo:
            file_id = message.photo.file_id  
            # Strict validation filter rule: Capture only the first line
            story_name = message.caption.split("\n")[0].strip() if message.caption else "Untitled Story"
        elif message.text:
            story_name = message.text.split("\n")[0].strip() # Line split parsing safely
        else:
            return await message.reply_text("❌ Please ek valid text naam ya photo bhejein:")

        ADMIN_STORY_STATES[user_id] = {
            "step": "get_demo",
            "story_name": story_name,
            "file_id": file_id
        }
        return await message.reply_text("🔗 <b>ᴅᴇᴍᴏ ʟɪɴᴋ:</b>\nDemo channel ya video link dein (Ya 'skip' likhein):", parse_mode=enums.ParseMode.HTML)

    # STEP B: DEMO COUPLING LINKS
    elif current_step == "get_demo":
        demo = None if (message.text and message.text.lower() == 'skip') else message.text
        
        state["demo_link"] = demo
        state["step"] = "get_final"
        ADMIN_STORY_STATES[user_id] = state
        
        return await message.reply_text("🤖 <b>... ғɪɴᴀʟ ʙᴏᴛ ʟɪɴᴋ ...:</b>\nPayment ke baad milne wala main link dein:", parse_mode=enums.ParseMode.HTML)

    # STEP C: FINAL PAYLOAD ACCESS LINKS
    elif current_step == "get_final":
        if not message.text:
            return await message.reply_text("❌ Please ek valid final link text bhejein:")
            
        state["bot_link"] = message.text
        state["step"] = "get_price"
        ADMIN_STORY_STATES[user_id] = state
        
        return await message.reply_text("💰 <b>ᴘʀɪᴄᴇ:</b>\nSirf number likhein (Example: 49):", parse_mode=enums.ParseMode.HTML)

    # STEP D: PRICING VALIDATION & DB TEMPORARY SAVE
    elif current_step == "get_price":
        if not message.text or not message.text.isdigit():
            return await message.reply_text("❌ Price sirf number mein likhein:")

        price = message.text
        story_id = str(uuid.uuid4())[:10] 
        ADMIN_STORY_STATES.pop(user_id, None) # Clear conversation memory map

        # Async Motor engine write block to db collection instance
        await db.db.channels_col.insert_one({
            "item_id": story_id,
            "story_name": state["story_name"],
            "demo_link": state["demo_link"],
            "bot_link": state["bot_link"],
            "price": price,
            "file_id": state["file_id"], 
            "type": "story",
            "status": "pending" 
        })

        # Platform selector interface (Strict lowercase data distribution mapping)
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎧 pocket", callback_data=f"src_pocket_{story_id}"),
                InlineKeyboardButton("📚 pratilipi", callback_data=f"src_pratilipi_{story_id}")
            ]
        ])

        await message.reply_text(
            "📂 <b>ᴄᴀᴛᴇɢᴏʀʏ sᴇʟᴇᴄᴛ ᴋᴀʀᴇɪɴ:</b>\nYeh story kiski hai?", 
            reply_markup=markup, 
            parse_mode=enums.ParseMode.HTML
        )


# --- 3. PLATFORM ASSIGNMENT ROUTER HANDLER ---
@Client.on_callback_query(filters.regex("^src_"))
async def save_story_with_source(client, call):
    if call.from_user.id != config.ADMIN_ID:
        return await call.answer("Unauthorized!", show_alert=True)

    parts = call.data.split('_')
    platform = "pocket" if parts[1] == "pocket" else "pratilipi"
    story_id = parts[2]

    # Asynchronously update document, unset pending status flag
    story_data = await db.db.channels_col.find_one_and_update(
        {"item_id": story_id, "status": "pending"},
        {"$set": {"source": platform}, "$unset": {"status": ""}},
        return_document=True
    )

    if not story_data:
        return await call.answer("❌ Session expired ya data nahi mila!", show_alert=True)

    try:
        await call.message.delete()
    except:
        pass

    bot_info = await client.get_me()
    share_link = f"https://t.me/{bot_info.username}?start={story_id}"
    
    res = (
        f"✅ <b>sᴛᴏʀʏ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b>\n"
        f"────────────────────\n"
        f"📖 Name: <b>{story_data['story_name']}</b>\n"
        f"📂 Platform: <code>{platform}</code>\n"
        f"💰 Price: <b>₹{story_data['price']}</b>\n"
        f"🖼️ Media: <b>{'Saved' if story_data['file_id'] else 'No Photo'}</b>\n\n"
        f"🔗 <b>ʏᴏᴜʀ sʜᴀʀᴇ ʟɪɴᴋ:</b>\n<code>{share_link}</code>\n"
        f"────────────────────\n"
        f"➔ Is link ko copy karke promote karein."
    )
    
    if story_data['file_id']:
        await client.send_photo(chat_id=call.message.chat.id, photo=story_data['file_id'], caption=res, parse_mode=enums.ParseMode.HTML)
    else:
        await client.send_message(chat_id=call.message.chat.id, text=res, parse_mode=enums.ParseMode.HTML)
