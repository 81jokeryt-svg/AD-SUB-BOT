# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import time
import urllib.parse
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardRemove
)
from plugins.dbusers import db  # Database integration instance
import config

# Global processing tracking to monitor screenshot submissions
USER_PAYMENT_STATES = {}

# ===================================================
# --- EXTRA CONFIG: FRESH START MENU RE-LOAD ---
# ===================================================
async def send_home_menu(client, chat_id):
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("« ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_to_start")]
    ])
    await client.send_message(
        chat_id=chat_id,
        text="❌ <b>ᴘᴀỹᴍᴇɴᴛ ᴄᴀɴᴄᴇʟʟᴇᴅ!</b>\n\nAapka current payment process rok diya gaya hai. Aap niche diye gaye menu se fir se shuru kar sakte hain:",
        reply_markup=markup,
        parse_mode=enums.ParseMode.HTML
    )


# --- 1. UNIFIED PAYMENT GATEWAY ROUTER (REDIRECTED FROM CONFIRM BUTTON) ---
@Client.on_callback_query(filters.regex("^pay_"))
async def confirm_step(client, call):
    """Deep Link ya Keyboard dono se Confirm dabane par ek jaisa Secure Checkout layout khulega"""
    db_id = call.data.split('_')[1]
    await call.answer("🔒 Securing connection Gateway...", show_alert=False)
    
    # Motor connection lookup matching core schema references
    data = await db.db.channels_col.find_one({"item_id": db_id}) or \
           await db.db.channels_col.find_one({"channel_id": int(db_id) if db_id.replace('-','').isdigit() else 0})
    
    if not data: 
        return await call.answer(f"❌ Data not found! (ID: {db_id})", show_alert=True)

    # Dynamic pricing validation rules setup
    if data.get('is_combo'):
        price = data['price']
        display_name = data.get('combo_name', 'Premium Combo')
        mins = "manual"
    elif 'story_name' in data:
        price = data['price']
        display_name = data.get('story_name').split("\n")[0].strip()
        mins = "manual"
    else:
        mins = "manual"  
        price = data.get('price', '49')
        display_name = data.get('name', 'Premium Channel')
    
    # Premium Layout with Razorpay (Maintenance Alert mapped) & Manual Payment Selection
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 PAY VIA RAZORPAY", callback_data=f"razor_alert_{db_id}")],
        [InlineKeyboardButton("📸 PAY VIA QR SCAN", callback_data=f"man_{db_id}_{mins}_qr")],
        [InlineKeyboardButton("📲 PAY VIA UPI ID", callback_data=f"man_{db_id}_{mins}_upi")],
        [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴘᴀỹᴍᴇɴᴛ", callback_data="cancel_payment")]
    ])
    
    text = (
        "📊 <code>Gateway option select karke payment complete karein.</code>\n\n"
        "| 🔒 <b><u>sᴇᴄᴜʀᴇ ᴄʜᴇᴄᴋᴏᴜᴛ</u></b>\n"
        "──────────────────────────\n"
        f"📦 <b>ɪᴛᴇᴍ:</b> <code>{display_name}</code>\n"
        f"💰 <b>ᴛᴏᴛᴀʟ ᴘʀɪᴄᴇ:</b> <b>₹{price}</b>\n\n"
        "✅ <b><u>ᴀᴜᴛᴏᴍᴀᴛɪᴄ ᴘᴀỹᴍᴇɴᴛ (...ʀᴀᴢᴏʀᴘᴀỹ)</u></b>\n"
        "➔ <b>ʙᴇɴᴇғɪᴛs:</b> Instant Access (No waiting)\n\n"
        "📝 <b><u>ᴍᴀɴᴜᴀʟ ᴘᴀỹᴍᴇɴᴛ (ǫʀ & ᴜᴘɪ ɪᴅ)</u></b>\n"
        "➔ <b>ᴘʀᴏᴄᴇss:</b> Pay ➔ Send Screenshot\n"
        "──────────────────────────"
    )
    
    try:
        await call.message.delete()
    except:
        pass

    await client.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)


# --- 2. RAZORPAY TEMPORARY MAINTENANCE POPUP CONTROLLER ---
@Client.on_callback_query(filters.regex("^razor_alert_"))
async def razorpay_alert_handler(client, call):
    await call.answer(
        text="⚠️ Razorpay Gateway is currently under maintenance!\n\nPlease choose QR SCAN or UPI ID to unlock instantly.", 
        show_alert=True
    )


# --- 3. MANUAL PAYMENT EXECUTION GATEWAY ---
@Client.on_callback_query(filters.regex("^man_"))
async def manual_pay(client, call):
    parts = call.data.split('_')
    mode = parts[-1]                
    mins = parts[-2]                
    db_id = "_".join(parts[1:-2]) 
    
    data = await db.db.channels_col.find_one({"item_id": db_id}) or \
           await db.db.channels_col.find_one({"channel_id": int(db_id) if db_id.replace('-','').isdigit() else 0})
    
    if not data:
        return await call.answer("❌ Data Error on Payment!", show_alert=True)

    price = data['price'] if (data.get('is_combo') or 'story_name' in data) else data.get('price', '49')
    display_name = data.get('combo_name') or data.get('story_name') or data.get('name', 'Premium Item')
    clean_title = display_name.split("\n")[0].strip()
        
    upi_string = f"upi://pay?pa={config.UPI_ID}&pn=Premium%20Store&am={price}&cu=INR&tn=Pay_{db_id}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=350x350&data={urllib.parse.quote(upi_string)}"
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ sᴜʙᴍɪᴛ sᴄʀᴇᴇɴsʜᴏᴛ", callback_data=f"paid_{db_id}_{mins}")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"pay_{db_id}")]
    ])

    try:
        await call.message.delete()
    except:
        pass

    if mode == "qr":
        qr_caption = (
            "📥 <b><u>[ ᴄᴏᴍᴘʟᴇᴛᴇ ᴘᴀỹᴍᴇɴᴛ ]</u></b>\n\n"
            "<b>🎯 Scan & Pay via QR Code</b>\n"
            "──────────────────────────\n"
            f"📦 <b>ɪᴛᴇᴍ:</b> <code>{clean_title}</code>\n"
            f"💰 <b>ᴀᴍᴏᴜɴᴛ:</b> <code>₹{price}</code>\n"
            "──────────────────────────\n"
            "➔ <i>Apne PhonePe, GPay, Paytm ya kisi bhi upi app se scan karke pay karein aur screenshot submit karein.</i>"
        )
        await client.send_photo(call.message.chat.id, qr_url, caption=qr_caption, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    else:
        upi_layout = (
            "📲 <b><u>[ ᴄ...ᴏᴍᴘʟᴇᴛᴇ ᴘᴀỹᴍᴇɴᴛ ]</u></b>\n\n"
            "<b>🎯 Copy UPI ID & Pay Manual</b>\n"
            "──────────────────────────\n"
            f"💳 <b>ᴜᴘɪ ɪᴅ:</b> <code>{config.UPI_ID}</code> (Tap to Copy)\n"
            f"📦 <b>ɪᴛᴇᴍ:</b> <code>{clean_title}</code>\n"
            f"💰 <b>ᴀᴍᴏᴜɴᴛ:</b> <code>₹{price}</code>\n"
            "──────────────────────────\n"
            "➔ <i>UPI ID copy karke pay karein aur niche diye button par click karke screenshot submit karein.</i>"
        )
        await client.send_message(call.message.chat.id, upi_layout, reply_markup=markup, parse_mode=enums.ParseMode.HTML)


# --- 4. DIRECT SCREENSHOT LISTENER SWITCH ---
@Client.on_callback_query(filters.regex("^paid_"))
async def handle_paid(client, call):
    parts = call.data.split('_')
    mins = parts[-1]
    db_id = "_".join(parts[1:-1])
    await call.answer()
    
    try:
        await call.message.delete()
    except:
        pass
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴘᴀỹᴍᴇɴᴛ", callback_data="cancel_payment")]
    ])
        
    await client.send_message(
        chat_id=call.message.chat.id, 
        text="📸 Payment ka <b>Screenshot</b> bhejein:\n\n➔ <i>Agar cancel karna chahte hain toh niche button par click karein ya chat me <code>/cancel</code> likhein.</i>", 
        reply_markup=markup, 
        parse_mode=enums.ParseMode.HTML
    )
    USER_PAYMENT_STATES[call.from_user.id] = {"item_id": db_id, "mins": mins, "awaiting_screenshot": True}


# Central tracking pipeline listening exclusively for screenshot upload actions
@Client.on_message(filters.private & filters.incoming, group=2)
async def payment_screenshot_handler(client, message):
    user_id = message.from_user.id
    state = USER_PAYMENT_STATES.get(user_id)
    
    if not state or not state.get("awaiting_screenshot"):
        return 
        
    if message.text and message.text.lower() in ['/cancel', 'cancel']:
        USER_PAYMENT_STATES.pop(user_id, None)
        return await send_home_menu(client, message.chat.id)

    if not message.photo:
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴘᴀỹᴍᴇɴᴛ", callback_data="cancel_payment")]
        ])
        return await message.reply_text(
            "❌ Please sirf Photo (Screenshot) bhejein!\nCancel karne ke liye <code>/cancel</code> likhein ya neeche click karein:", 
            reply_markup=markup, 
            parse_mode=enums.ParseMode.HTML
        )
    
    item_id = state["item_id"]
    mins = state["mins"]
    USER_PAYMENT_STATES.pop(user_id, None) 
    
    photo_id = message.photo.file_id
    data = await db.db.channels_col.find_one({"item_id": item_id}) or \
           await db.db.channels_col.find_one({"channel_id": int(item_id) if item_id.replace('-','').isdigit() else 0})
    
    if not data:
        return await message.reply_text("❌ Something went wrong, item not found!")

    display_name = data.get('combo_name') or data.get('story_name') or data.get('name')
    if display_name and "\n" in display_name:
        display_name = display_name.split("\n")[0].strip()

    await message.reply_text("⏳ <b>ʀᴇǫᴜᴇsᴛ sᴇɴᴛ!</b>\nAdmin check karke aapka access on kar dega.", parse_mode=enums.ParseMode.HTML)
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve", callback_data=f"app_{user_id}_{item_id}_{mins}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user_id}"), 
         InlineKeyboardButton("💬 Support", url=f"tg://openmessage?user_id={user_id}")]
    ])
    
    admin_text = f"📥 <b>ɴᴇᴡ ᴘᴀỹᴍᴇɴᴛ ʀᴇǫᴜᴇsᴛ</b>\n────────────────────\n👤 User ID: <code>{user_id}</code>\n📦 Item: <b>{display_name}</b>\n⏳ Plan: {mins if mins != 'manual' else 'Lifetime'}"
    await client.send_photo(chat_id=config.ADMIN_ID, photo=photo_id, caption=admin_text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)


@Client.on_callback_query(filters.regex("^cancel_payment$"))
async def process_inline_cancel(client, call):
    await call.answer("Process Cancelled!")
    USER_PAYMENT_STATES.pop(call.from_user.id, None)
    try:
        await call.message.delete()
    except:
        pass
    await send_home_menu(client, call.message.chat.id)


# --- 5. ADMIN APPROVAL DISPATCH SYSTEM ---
@Client.on_callback_query(filters.regex("^app_"))
async def admin_approve(client, call):
    parts = call.data.split('_')
    u_id = parts[1]
    mins = parts[-1]
    
    item_id = "_join".join(parts[2:-1]) if "_join" in call.data else "_".join(parts[2:-1])
    
    data = await db.db.channels_col.find_one({"item_id": item_id}) or \
           await db.db.channels_col.find_one({"channel_id": int(item_id) if item_id.replace('-','').isdigit() else 0})
    
    if not data: 
        return await call.answer("❌ Data not found on Approval!", show_alert=True)
    
    expiry = int(time.time()) + (int(mins) * 60) if mins != 'manual' else int(time.time()) + (365*24*60*60)
    inline_buttons = []

    # ─── CASE A: COMBO PACK DISTRIBUTION PIPELINE ───
    if data.get('is_combo') and 'channels_list' in data:
        msg = "🎁 <b>ᴄ...ᴏᴍʙᴏ ᴘᴀᴄᴋ ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n\nAapko sabhi linked channels ka access de diya gaya hai. Niche diye buttons se join karein:\n\n"
        for ch_id in data['channels_list']:
            await db.db.users_col.update_one({"user_id": int(u_id), "channel_id": int(ch_id)}, {"$set": {"expiry": expiry}}, upsert=True)
            try:
                invite = await client.create_chat_invite_link(int(ch_id), member_limit=1)
                ch_info = await db.db.channels_col.find_one({"channel_id": int(ch_id)})
                
                ch_title = ch_info.get('name') or ch_info.get('story_name') if ch_info else f"VIP Channel {ch_id}"
                if ch_title and "\n" in ch_title:
                    ch_title = ch_title.split("\n")[0].strip()
                
                inline_buttons.append([InlineKeyboardButton(f"📢 Join: {ch_title}", url=invite.invite_link)])
            except Exception as e:
                print(f"Combo Link Error: {e}")
        msg += "⚠️ <i>Links single-use hain, ek baar join hone ke baad automatic expire ho jayengi!</i>"

    # ─── CASE B: ROUTED GENERAL TELEGRAM CHANNEL ───
    elif data.get('type') == 'channel' or ('channel_id' in data and data.get('source') not in ['pocket', 'pratilipi'] and not data.get('is_combo')):
        target_channel = int(data['channel_id'])
        await db.db.users_col.update_one({"user_id": int(u_id), "channel_id": target_channel}, {"$set": {"expiry": expiry}}, upsert=True)
        try:
            invite = await client.create_chat_invite_link(chat_id=target_channel, member_limit=1)
            inline_buttons.append([InlineKeyboardButton("🔐 JOIN PREMIUM CHANNEL", url=invite.invite_link)])
            
            validity_display = data.get('validity', mins)
            msg = (
                f"✅ <b>ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n\n"
                f"📂 <b>ᴄʜᴀɴɴᴇʟ:</b> <b>{data.get('name', 'VIP Channel')}</b>\n"
                f"⏱️ <b>ᴠᴀʟɪᴅɪᴛỹ:</b> {validity_display if validity_display != 'manual' else 'Lifetime'}\n\n"
                f"Join karne ke liye neeche button par click karein:\n\n"
                f"⚠️ <i>Yeh link single use hai, ek baar use hone ke baad automatic expire ho jayegi!</i>"
            )
        except Exception as e: 
            print(f"Error: {e}")
            msg = "✅ <b>ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n\nBot link generate nahi kar saka, admin rights setup check karein."

    # ─── CASE C: PREMIUM STORY INTERNAL FLOW ───
    else:
        await db.db.users_col.update_one({"user_id": int(u_id), "channel_id": data.get('channel_id', 0)}, {"$set": {"expiry": expiry}}, upsert=True)
        target_link = data.get('bot_link') or data.get('final_link') or 'https://t.me'
        
        inline_buttons.append([InlineKeyboardButton("🚀 sᴛᴀʀᴛ sᴛᴏʀỹ", url=target_link)])
        
        raw_story_name = data.get('story_name', 'Premium Story')
        clean_story_name = raw_story_name.split('\n')[0].strip()
        platform_info = f"\n📂 Platform: <code>{data.get('source')}</code>" if data.get('source') else ""
        
        msg = (
            f"🎉 <b>ᴘᴀỹᴍᴇɴᴛ ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n"
            f"────────────────────\n"
            f"📖 <b>sᴛᴏʀỹ:</b> {clean_story_name}"
            f"{platform_info}\n"
            f"💰 <b>ᴘʀɪᴄɪɴɢ:</b> ₹{data.get('price', '49')}\n"
            f"────────────────────\n"
            f"➔ Niche diye gaye button par click karke apni full story access karein 👇"
        )

    try:
        markup = InlineKeyboardMarkup(inline_buttons)
        if 'story_name' in data and data.get('file_id') and data.get('type') != 'channel':
            await client.send_photo(chat_id=int(u_id), photo=data['file_id'], caption=msg, reply_markup=markup, protect_content=True)
        else:
            await client.send_message(chat_id=int(u_id), text=msg, reply_markup=markup, protect_content=True)
    except Exception as e:
        print(f"Delivery Error: {e}")
        
    admin_caption = f"✅ Approved for User: {u_id}"
    await client.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        caption=admin_caption
    )


@Client.on_callback_query(filters.regex("^rej_"))
async def admin_reject(client, call):
    u_id = call.data.split('_')[1]
    
    reject_caption = "❌ Payment Rejected!"
    await client.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        caption=reject_caption
    )
    await client.send_message(chat_id=int(u_id), text="❌ Aapka payment reject ho gaya hai. Support se baat karein.")
