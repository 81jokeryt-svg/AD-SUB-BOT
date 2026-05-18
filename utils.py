import logging
import asyncio
import os
import re
import random
import pytz
import aiohttp
import requests
import string
import json
import http.client
import time
from datetime import date, datetime
from config import SHORTLINK_API, SHORTLINK_URL, VERIFY_EXPIRE_TIME
from shortzy import Shortzy
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ग्लोबल डिक्शनरी यूज़र्स का डेटा स्टोर करने के लिए
TOKENS = {}
VERIFIED = {}

# 🌟 NEW: यूज़र्स की dynamic settings save karne ke liye global dictionary
SETTINGS = {}

def get_status_icon(flag):
    return "✅" if flag else "❌"

# 🌟 NEW: Dynamic Settings Keyboard Generator for Venom File Store
def generate_settings_keyboard(user_id):
    # Agar user ki pehle se koi settings save nahi hai, toh default set karein
    if user_id not in SETTINGS:
        SETTINGS[user_id] = {
            "link_shortener": False,
            "token_verification": False,
            "custom_caption": True,
            "force_subscribe": True,
            "auto_delete": False,
            "protect_content": False,
            "stream_download": False
        }
    
    settings = SETTINGS[user_id]
    
    keyboard = [
        [InlineKeyboardButton("⭐ PREMIUM PLAN", callback_data="premium_plan")],
        [InlineKeyboardButton(f"🔗 LINK SHORTENER - {get_status_icon(settings['link_shortener'])}", callback_data="toggle_link_shortener")],
        [InlineKeyboardButton(f"🎟️ TOKEN VERIFICATION - {get_status_icon(settings['token_verification'])}", callback_data="toggle_token_verification")],
        [InlineKeyboardButton(f"📝 CUSTOM CAPTION - {get_status_icon(settings['custom_caption'])}", callback_data="toggle_custom_caption")],
        [InlineKeyboardButton(f"📢 CUSTOM FORCE SUBSCRIBE - {get_status_icon(settings['force_subscribe'])}", callback_data="toggle_force_subscribe")],
        [InlineKeyboardButton(f"🗑️ AUTO DELETE - {get_status_icon(settings['auto_delete'])}", callback_data="toggle_auto_delete")],
        [InlineKeyboardButton("🔗 PERMANENT LINK", callback_data="permanent_link")],
        [InlineKeyboardButton(f"🔒 PROTECT CONTENT - {get_status_icon(settings['protect_content'])}", callback_data="toggle_protect_content")],
        [InlineKeyboardButton(f"📥 STREAM/DOWNLOAD - {get_status_icon(settings['stream_download'])}", callback_data="toggle_stream_download")],
        [InlineKeyboardButton("◀️ BACK", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def get_verify_shorted_link(link):
    if SHORTLINK_URL == "api.shareus.io":
        url = f'https://{SHORTLINK_URL}/easy_api'
        params = {
            "key": SHORTLINK_API,
            "link": link,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, raise_for_status=True, ssl=False) as response:
                    data = await response.text()
                    return data
        except Exception as e:
            logger.error(e)
            return link
    else:
        shortzy = Shortzy(api_key=SHORTLINK_API, base_site=SHORTLINK_URL)
        link = await shortzy.convert(link)
        return link

async def check_token(bot, userid, token):
    user = await bot.get_users(userid)
    if user.id in TOKENS.keys():
        TKN = TOKENS[user.id]
        if token in TKN.keys():
            is_used = TKN[token]
            if is_used == True:
                return False  # टोकन पहले ही यूज़ हो चुका है
            else:
                return True   # टोकन वैलिड है
    return False

async def get_token(bot, userid, link):
    user = await bot.get_users(userid)
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=7))
    
    # 🌟 FIX: यूज़र की पुरानी टोकन हिस्ट्री डिलीट न हो, इसलिए डिक्शनरी चेक करके अपडेट कर रहे हैं
    if user.id not in TOKENS:
        TOKENS[user.id] = {}
    TOKENS[user.id][token] = False
    
    link = f"{link}verify-{user.id}-{token}"
    shortened_verify_url = await get_verify_shorted_link(link)
    return str(shortened_verify_url)

async def verify_user(bot, userid, token):
    user = await bot.get_users(userid)
    
    # टोकन को Used (True) मार्क करें
    if user.id not in TOKENS:
        TOKENS[user.id] = {}
    TOKENS[user.id][token] = True
    
    # 🌟 UPDATED: वेरिफिकेशन सफल होने पर करंट टाइमस्टैम्प (Seconds में) सेव करें
    VERIFIED[user.id] = time.time()

async def check_verification(bot, userid):
    user = await bot.get_users(userid)
    
    # 🌟 NEW LOGIC: Agar admin/user ne Token Verification settings se OFF (❌) kiya hua hai,
    # toh hamesha True return karein (matlab bypass kar de, verification na maange)
    user_settings = SETTINGS.get(user.id, {})
    if not user_settings.get("token_verification", False):
        return True # Verification is turned OFF, allow user directly.

    if user.id in VERIFIED.keys():
        last_verified = VERIFIED[user.id]
        # 🌟 UPDATED: करंट टाइम से पिछले वेरिफिकेशन टाइम का अंतर निकाल कर एक्सपायरी चेक करें
        if (time.time() - last_verified) > VERIFY_EXPIRE_TIME:
            return False  # Verification Expire ho gaya
        else:
            return True   # Verification Valid hai
    else:
        return False
