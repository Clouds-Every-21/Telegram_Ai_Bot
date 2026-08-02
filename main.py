# ============================================================
# 🚀 ربات تلگرام با هوش مصنوعی OpenRouter - نسخه پایتون
# ============================================================

import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import httpx
from datetime import datetime

# ============================================================
# 📋 بخش ۱: تنظیمات اولیه
# ============================================================

BOT_TOKEN = '8852045775:AAGmMo87GVigfKbiMyA442AQK_7nlNUwzq4'
OPENROUTER_API_KEY = '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'
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تاریخچه چت کاربران
chat_history = {}

# ایموجی‌ها
EMOJIS = {
    'chat': '💬',
    'analyze': '📊',
    'translate': '🔄',
    'prompt': '✨',
    'summarize': '📝',
    'search': '🔍',
    'help': '📖',
    'copy': '📋',
    'new_chat': '🔄',
    'back': '🔙',
    'welcome': '🤖',
    'success': '✅',
    'error': '❌',
    'loading': '⏳',
    'info': 'ℹ️'
}

# ============================================================
# 📋 بخش ۲: توابع OpenRouter
# ============================================================

async def call_openrouter(messages, model='google/gemini-3.5-flash'):
    """ارسال درخواست به OpenRouter"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                    'HTTP-Referer': 'https://t.me/PurpleAI1bot',
                    'X-Title': 'Purple AI Bot'
                },
                json={
                    'model': model,
                    'messages': messages,
                    'max_tokens': 800,
                    'temperature': 0.7
                }
            )
            
            if response.status_code == 401 or response.status_code == 403:
                return '❌ API Key معتبر نیست. لطفاً کلید خود را بررسی کنید.'
            elif response.status_code == 429:
                return '⏳ محدودیت درخواست رسیده. لطفاً چند دقیقه صبر کنید.'
            elif response.status_code != 200:
                logger.error(f'OpenRouter Error: {response.text}')
                return '❌ خطا در ارتباط با سرور. لطفاً بعداً تلاش کنید.'
            
            data = response.json()
            if data.get('choices') and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
            return 'پاسخی دریافت نشد.'
            
    except httpx.TimeoutException:
        return '⏳ زمان پاسخ‌گویی به پایان رسید. لطفاً دوباره تلاش کنید.'
    except Exception as e:
        logger.error(f'Error in call_openrouter: {e}')
        return await call_openrouter_fallback(messages)

async def call_openrouter_fallback(messages):
    """Fallback به مدل دیگر"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                    'HTTP-Referer': 'https://t.me/PurpleAI1bot',
                    'X-Title': 'Purple AI Bot'
                },
                json={
                    'model': 'google/gemini-2.5-flash',
                    'messages': messages,
                    'max_tokens': 800,
                    'temperature': 0.7
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('choices') and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content']
            
            return 'متاسفانه خطایی رخ داده است. لطفاً دوباره تلاش کنید.'
            
    except Exception as e:
        logger.error(f'Error in fallback: {e}')
        return '❌ خطا در ارتباط با سرور. لطفاً بعداً تلاش کنید.'

# ============================================================
# 📋 بخش ۳: منوها و کیبوردها
# ============================================================

def main_menu_keyboard():
    """کیبورد منوی اصلی"""
    keyboard = [
        [KeyboardButton(f"{EMOJIS['chat']} چت"), KeyboardButton(f"{EMOJIS['analyze']} تحلیل")],
        [KeyboardButton(f"{EMOJIS['translate']} ترجمه"), KeyboardButton(f"{EMOJIS['prompt']} پرامپت")],
        [KeyboardButton(f"{EMOJIS['summarize']} خلاصه"), KeyboardButton(f"{EMOJIS['search']} جستجو")],
        [KeyboardButton(f"{EMOJIS['help']} راهنما")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def back_to_main_keyboard():
    """کیبورد بازگشت به منو"""
    keyboard = [[KeyboardButton(f"{EMOJIS['back']} بازگشت به منو")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def message_buttons(chat_id):
    """دکمه‌های زیر پیام"""
    keyboard = [
        [
            InlineKeyboardButton(f"{EMOJIS['copy']} کپی متن", callback_data=f"copy_{chat_id}"),
            InlineKeyboardButton(f"{EMOJIS['new_chat']} چت جدید", callback_data=f"newchat_{chat_id}")
        ],
        [InlineKeyboardButton(f"{EMOJIS['back']} بازگشت به منو", callback_data="backtomenu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def simple_buttons():
    """دکمه‌های ساده"""
    keyboard = [[InlineKeyboardButton(f"{EMOJIS['back']} بازگشت به منو", callback_data="backtomenu")]]
    return InlineKeyboardMarkup(keyboard)

# ============================================================
# 📋 بخش ۴: هندلرهای اصلی
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /start"""
    chat_id = update.effective_chat.id
    
    welcome_message = f"""
{EMOJIS['welcome']} **به ربات Purple AI خوش آمدید!**

من یک ربات هوشمند هستم که با استفاده از OpenRouter و مدل‌های مختلف می‌توانم:
• به سوالات شما پاسخ دهم
• متون را ترجمه و خلاصه کنم
• پرامپت‌های حرفه‌ای تولید کنم
• تحلیل حرفه‌ای متن ارائه دهم

از منوی پایین برای شروع استفاده کنید یا دستورات را با /help ببینید.
    """
    
    await update.message.reply_text(
        welcome_message.strip(),
        parse_mode='HTML',
        reply_markup=main_menu_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /help"""
    chat_id = update.effective_chat.id
    
    help_message = f"""
{EMOJIS['help']} **راهنمای کامل ربات**

📌 **دستورات:**
• /start - شروع مجدد ربات
• /help - نمایش این راهنما
• /about - اطلاعات ربات
• /analyze [متن] - تحلیل حرفه‌ای متن
• /translate [متن] to [زبان] - ترجمه متن
• /summarize [متن] - خلاصه‌سازی متن
• /prompt [توضیحات] - تولید پرامپت

📌 **قابلیت‌های ویژه:**
• چت هوشمند با حفظ تاریخچه
• پاسخ‌های مختصر و دقیق
• دکمه‌های کپی و مدیریت چت

💡 **نکته:** برای استفاده از منو، روی دکمه‌های پایین کلیک کنید.
    """
    
    await update.message.reply_text(
        help_message.strip(),
        parse_mode='HTML',
        reply_markup=main_menu_keyboard()
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /about"""
    chat_id = update.effective_chat.id
    
    about_message = f"""
{EMOJIS['info']} **درباره ربات**

**نام:** Purple AI
**نسخه:** 3.0
**موتور هوش مصنوعی:** OpenRouter
**مدل‌های پشتیبانی شده:** Gemini, Claude, GPT و...
**پلتفرم:** Python + Telegram Bot API

**ویژگی‌ها:**
• چت هوشمند با حفظ تاریخچه
• ترجمه و خلاصه‌سازی
• تولید پرامپت حرفه‌ای
• پاسخ‌های مختصر و دقیق

**توسعه‌دهنده:** تیم Purple AI
    """
    
    await update.message.reply_text(
        about_message.strip(),
        parse_mode='HTML',
        reply_markup=main_menu_keyboard()
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های متنی"""
    chat_id = update.effective_chat.id
    text = update.message.text
    username = update.effective_user.first_name or 'کاربر'
    
    # بررسی دستورات
    if text.startswith('/'):
        return
    
    # بررسی دکمه‌های منو
    if text == f"{EMOJIS['chat']} چت":
        await chat_mode(update, context)
        return
    elif text == f"{EMOJIS['analyze']} تحلیل":
        await update.message.reply_text(
            f"{EMOJIS['analyze']} لطفاً متنی که می‌خواهید تحلیل کنم را ارسال کنید:",
            reply_markup=back_to_main_keyboard()
        )
        return
    elif text == f"{EMOJIS['translate']} ترجمه":
        await update.message.reply_text(
            f"{EMOJIS['translate']} لطفاً متن و زبان مقصد را به این فرمت وارد کنید:\n\n"
            f"`/translate [متن] to [زبان]`\n\n"
            f"مثال: `/translate سلام to English`",
            parse_mode='Markdown',
            reply_markup=back_to_main_keyboard()
        )
        return
    elif text == f"{EMOJIS['prompt']} پرامپت":
        await update.message.reply_text(
            f"{EMOJIS['prompt']} لطفاً توضیحات پرامپت مورد نظر را به این فرمت وارد کنید:\n\n"
            f"`/prompt [توضیحات]`",
            parse_mode='Markdown',
            reply_markup=back_to_main_keyboard()
        )
        return
    elif text == f"{EMOJIS['summarize']} خلاصه":
        await update.message.reply_text(
            f"{EMOJIS['summarize']} لطفاً متنی که می‌خواهید خلاصه کنم را به این فرمت وارد کنید:\n\n"
            f"`/summarize [متن]`",
            parse_mode='Markdown',
            reply_markup=back_to_main_keyboard()
        )
        return
    elif text == f"{EMOJIS['search']} جستجو":
        await update.message.reply_text(
            f"{EMOJIS['search']} لطفاً عبارت جستجو را به این فرمت وارد کنید:\n\n"
            f"`/search [عبارت]`",
            parse_mode='Markdown',
            reply_markup=back_to_main_keyboard()
        )
        return
    elif text == f"{EMOJIS['help']} راهنما" or text == f"{EMOJIS['back']} بازگشت به منو":
        await help_command(update, context)
        return
    
    # حالت چت هوشمند
    await chat_mode(update, context, text)

async def chat_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message=None):
    """حالت چت هوشمند"""
    chat_id = update.effective_chat.id
    
    if not user_message:
        chat_prompt = f"""
{EMOJIS['chat']} **حالت چت فعال است!**

لطفاً سوالتان را بپرسید. من با استفاده از OpenRouter و مدل‌های مختلف پاسخ می‌دهم.
تاریخچه آخرین ۱۰ پیام برای پاسخ‌های بهتر حفظ می‌شود.

برای شروع چت جدید، روی دکمه "چت جدید" کلیک کنید.
        """
        await update.message.reply_text(
            chat_prompt.strip(),
            parse_mode='HTML',
            reply_markup=back_to_main_keyboard()
        )
        return
    
    try:
        # ارسال پیام "در حال پردازش"
        loading_msg = await update.message.reply_text(f"{EMOJIS['loading']} در حال پردازش...")
        
        # دریافت تاریخچه
        history = chat_history.get(chat_id, [])
        
        # ساخت پیام‌ها
        messages = [
            {
                'role': 'system',
                'content': 'شما یک دستیار هوشمند و حرفه‌ای هستید. پاسخ‌های شما مختصر، دقیق و با لحن دوستانه است.'
            }
        ]
        
        if history:
            for msg in history:
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        messages.append({
            'role': 'user',
            'content': user_message
        })
        
        # دریافت پاسخ
        response = await call_openrouter(messages)
        
        # ذخیره در تاریخچه
        history.append({'role': 'user', 'content': user_message})
        history.append({'role': 'assistant', 'content': response})
        
        if len(history) > 20:
            history = history[-20:]
        
        chat_history[chat_id] = history
        
        # حذف پیام "در حال پردازش"
        await loading_msg.delete()
        
        # ارسال پاسخ
        await update.message.reply_text(
            response,
            parse_mode='HTML',
            reply_markup=message_buttons(chat_id)
        )
        
    except Exception as e:
        logger.error(f'Error in chat_mode: {e}')
        await update.message.reply_text(
            f"{EMOJIS['error']} خطا در پردازش پیام. لطفاً دوباره تلاش کنید."
        )

# ============================================================
# 📋 بخش ۵: پردازش دستورات
# ============================================================

async def process_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش دستورات"""
    chat_id = update.effective_chat.id
    text = update.message.text
    parts = text.split(' ')
    cmd = parts[0].lower()
    args = ' '.join(parts[1:])
    
    if cmd == '/start':
        await start_command(update, context)
    
    elif cmd == '/help':
        await help_command(update, context)
    
    elif cmd == '/about':
        await about_command(update, context)
    
    elif cmd == '/analyze':
        if not args:
            await update.message.reply_text(
                f"{EMOJIS['analyze']} لطفاً متنی برای تحلیل وارد کنید.\n"
                f"مثال: `/analyze امروز روز خوبی بود`",
                parse_mode='Markdown'
            )
            return
        
        loading_msg = await update.message.reply_text(f"{EMOJIS['loading']} در حال تحلیل متن...")
        
        messages = [
            {
                'role': 'system',
                'content': 'شما یک تحلیلگر حرفه‌ای متن هستید. پاسخ‌های شما باید ساختارمند و دقیق باشد.'
            },
            {
                'role': 'user',
                'content': f"""
لطفاً متن زیر را به صورت حرفه‌ای تحلیل کن و خروجی را با ساختار زیر ارائه بده:

📌 **موضوع اصلی:**
[موضوع اصلی متن]

🎯 **احساسات غالب:**
[احساسات موجود در متن]

🔑 **کلمات کلیدی:**
[۵-۷ کلمه کلیدی مهم]

💡 **نکات مهم:**
[۳-۵ نکته کلیدی از متن]

📋 **خلاصه:**
[خلاصه‌ای مختصر و مفید در ۲-۳ خط]

🏷️ **دسته‌بندی:**
[دسته‌بندی موضوعی متن]

متن برای تحلیل:
{args}
"""
            }
        ]
        
        response = await call_openrouter(messages)
        await loading_msg.delete()
        
        await update.message.reply_text(
            response,
            parse_mode='HTML',
            reply_markup=message_buttons(chat_id)
        )
    
    elif cmd == '/translate':
        if not args:
            await update.message.reply_text(
                f"{EMOJIS['translate']} لطفاً متن و زبان مقصد را وارد کنید.\n"
                f"مثال: `/translate سلام to English`",
                parse_mode='Markdown'
            )
            return
        
        to_index = args.lower().rfind(' to ')
        if to_index == -1:
            await update.message.reply_text(
                f"{EMOJIS['error']} فرمت اشتباه. از این فرمت استفاده کنید:\n"
                f"`/translate [متن] to [زبان]`",
                parse_mode='Markdown'
            )
            return
        
        text_to_translate = args[:to_index].strip()
        target_lang = args[to_index + 4:].strip()
        
        loading_msg = await update.message.reply_text(f"{EMOJIS['loading']} در حال ترجمه به {target_lang}...")
        
        messages = [
            {
                'role': 'system',
                'content': f'شما یک مترجم حرفه‌ای هستید. متن را به {target_lang} ترجمه کنید و فقط متن ترجمه شده را برگردانید.'
            },
            {
                'role': 'user',
                'content': text_to_translate
            }
        ]
        
        response = await call_openrouter(messages)
        await loading_msg.delete()
        
        await update.message.reply_text(
            f"{EMOJIS['translate']} **ترجمه به {target_lang}:**\n\n{response}",
            parse_mode='HTML',
            reply_markup=message_buttons(chat_id)
        )
    
    elif cmd == '/summarize':
        if not args:
            await update.message.reply_text(
                f"{EMOJIS['summarize']} لطفاً متنی برای خلاصه‌سازی وارد کنید.\n"
                f"مثال: `/summarize متن طولانی...`",
                parse_mode='Markdown'
            )
            return
        
        loading_msg = await update.message.reply_text(f"{EMOJIS['loading']} در حال خلاصه‌سازی متن...")
        
        messages = [
            {
                'role': 'system',
                'content': 'شما یک متخصص خلاصه‌سازی متن هستید. متن را به صورت مختصر و مفید خلاصه کنید و نکات کلیدی را ذکر کنید.'
            },
            {
                'role': 'user',
                'content': args
            }
        ]
        
        response = await call_openrouter(messages)
        await loading_msg.delete()
        
        await update.message.reply_text(
            f"{EMOJIS['summarize']} **خلاصه متن:**\n\n{response}",
            parse_mode='HTML',
            reply_markup=message_buttons(chat_id)
        )
    
    elif cmd == '/prompt':
        if not args:
            await update.message.reply_text(
                f"{EMOJIS['prompt']} لطفاً توضیحات پرامپت مورد نظر را وارد کنید.\n"
                f"مثال: `/prompt یک داستان علمی تخیلی درباره آینده`",
                parse_mode='Markdown'
            )
            return
        
        loading_msg = await update.message.reply_text(f"{EMOJIS['loading']} در حال تولید پرامپت...")
        
        messages = [
            {
                'role': 'system',
                'content': 'شما یک متخصص تولید پرامپت هستید. بر اساس توضیحات کاربر، یک پرامپت حرفه‌ای و دقیق برای استفاده در هوش مصنوعی تولید کنید.'
            },
            {
                'role': 'user',
                'content': args
            }
        ]
        
        response = await call_openrouter(messages)
        await loading_msg.delete()
        
        await update.message.reply_text(
            f"{EMOJIS['prompt']} **پرامپت تولید شده:**\n\n{response}",
            parse_mode='HTML',
            reply_markup=message_buttons(chat_id)
        )
    
    elif cmd == '/search':
        if not args:
            await update.message.reply_text(
                f"{EMOJIS['search']} لطفاً عبارت جستجو را وارد کنید.\n"
                f"مثال: `/search آب و هوای تهران`",
                parse_mode='Markdown'
            )
            return
        
        loading_msg = await update.message.reply_text(f"{EMOJIS['loading']} در حال جستجو...")
        
        messages = [
            {
                'role': 'system',
                'content': 'شما یک دستیار جستجو هستید. بر اساس دانش خود، اطلاعات مفید و به‌روز درباره موضوع مورد نظر ارائه دهید.'
            },
            {
                'role': 'user',
                'content': args
            }
        ]
        
        response = await call_openrouter(messages)
        await loading_msg.delete()
        
        await update.message.reply_text(
            f"{EMOJIS['search']} **نتایج جستجو برای \"{args}\":**\n\n{response}",
            parse_mode='HTML',
            reply_markup=message_buttons(chat_id)
        )
    
    else:
        await update.message.reply_text(
            f"{EMOJIS['error']} دستور ناشناخته. برای مشاهده راهنما از /help استفاده کنید."
        )

# ============================================================
# 📋 بخش ۶: پردازش Callback Query
# ============================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش کلیک روی دکمه‌ها"""
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    data = query.data
    
    if data == 'backtomenu':
        await query.edit_message_text(
            f"{EMOJIS['help']} **راهنمای کامل ربات**\n\n"
            f"📌 **دستورات:**\n"
            f"• /start - شروع مجدد ربات\n"
            f"• /help - نمایش این راهنما\n"
            f"• /about - اطلاعات ربات\n"
            f"• /analyze [متن] - تحلیل حرفه‌ای متن\n"
            f"• /translate [متن] to [زبان] - ترجمه متن\n"
            f"• /summarize [متن] - خلاصه‌سازی متن\n"
            f"• /prompt [توضیحات] - تولید پرامپت\n\n"
            f"💡 **نکته:** برای استفاده از منو، روی دکمه‌های پایین کلیک کنید.",
            parse_mode='HTML',
            reply_markup=main_menu_keyboard()
        )
    
    elif data.startswith('newchat_'):
        chat_history[chat_id] = []
        await query.edit_message_text(
            f"{EMOJIS['success']} تاریخچه چت پاک شد. می‌توانید چت جدیدی را شروع کنید.",
            reply_markup=main_menu_keyboard()
        )
    
    elif data.startswith('copy_'):
        await query.edit_message_text(
            f"{EMOJIS['success']} برای کپی کردن متن، آن را انتخاب کنید و کپی کنید.",
            reply_markup=simple_buttons()
        )

# ============================================================
# 📋 بخش ۷: اجرای اصلی
# ============================================================

def main():
    """تابع اصلی اجرا"""
    # ایجاد اپلیکیشن
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن هندلرها
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('about', about_command))
    application.add_handler(CommandHandler('analyze', process_command))
    application.add_handler(CommandHandler('translate', process_command))
    application.add_handler(CommandHandler('summarize', process_command))
    application.add_handler(CommandHandler('prompt', process_command))
    application.add_handler(CommandHandler('search', process_command))
    
    # هندلر پیام‌ها
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # هندلر دکمه‌ها
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # شروع ربات
    print('🤖 ربات Purple AI راه‌اندازی شد!')
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
