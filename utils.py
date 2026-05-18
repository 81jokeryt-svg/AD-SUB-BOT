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
from plugins.dbusers import db  # MongoDB layer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global dict for tokens validation
TOKENS = {}

def get_status_icon(flag):
    return "✅" if flag else "❌"

def generate_settings_keyboard(settings):
    keyboard = [
        [InlineKeyboardButton("⭐ PREMIUM PLAN", callback_data="premium_plan")],
        [InlineKeyboardButton(f"🔗 LINK SHORTENER - {get_status_icon(settings.get('link_shortener', False))}", callback_data="toggle_link_shortener")],
        [InlineKeyboardButton(f"🎟️ TOKEN VERIFICATION - {get_status_icon(settings.get('token_verification', False))}", callback_data="toggle_token_verification")],
        [InlineKeyboardButton(f"📝 CUSTOM CAPTION - {get_status_icon(settings.get('custom_caption', False))}", callback_data="toggle_custom_caption")],
        [InlineKeyboardButton(f"📢 CUSTOM FORCE SUBSCRIBE - {get_status_icon(settings.get('force_subscribe', False))}", callback_data="toggle_force_subscribe")],
        [InlineKeyboardButton(f"🗑️ AUTO DELETE - {get_status_icon(settings.get('auto_delete', False))}", callback_data="toggle_auto_delete")],
        [InlineKeyboardButton("🔗 PERMANENT LINK", callback_data="permanent_link")],
        [InlineKeyboardButton(f"🔒 PROTECT CONTENT - {get_status_icon(settings.get('protect_content', False))}", callback_data="toggle_protect_content")],
        [InlineKeyboardButton(f"📥 STREAM/DOWNLOAD - {get_status_icon(settings.get('stream_download', False))}", callback_data="toggle_stream_download")],
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
    if int(userid) in TOKENS.keys():
        TKN = TOKENS[int(userid)]
        if token in TKN.keys():
            is_used = TKN[token]
            if is_used == True:
                return False  
            else:
                return True   
    return False

# 🌟 FIXED: Ab ye function khali link nahi, balki original file data payload sath me lekar short link banayega
async def get_token(bot, userid, username, file_data):
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=7))
    
    if int(userid) not in TOKENS:
        TOKENS[int(userid)] = {}
    TOKENS[int(userid)][token] = False
    
    # [FIX]: Sahi token format jo file details ko memory me hold rakhega verification ke baad ke liye
    link = f"https://telegram.me/{username}?start=verify-{userid}-{token}-{file_data}"
    shortened_verify_url = await get_verify_shorted_link(link)
    return str(shortened_verify_url)

async def verify_user(bot, userid, token):
    if int(userid) not in TOKENS:
        TOKENS[int(userid)] = {}
    TOKENS[int(userid)][token] = True
    await db.update_verify_time(int(userid), time.time())

async def check_verification(bot, userid):
    user_settings = await db.get_user_settings(int(userid))
    if not user_settings.get("token_verification", False):
        return True 

    last_verified = await db.get_verify_time(int(userid))
    if last_verified > 0:
        if (time.time() - last_verified) > VERIFY_EXPIRE_TIME:
            return False  
        else:
            return True   
    else:
        return False
