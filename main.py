import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from brain import HalolScannerEngine, INGREDIENTS_DB
from PIL import Image
import pytesseract
import db  # <--- Yangi baza faylimizni ulaymiz

# --- ⚠️ SOZLAMALAR ---
BOT_TOKEN = "8555323979:AAF41Dc67DbyH1Rpcj6n3PeubPInoFxISmk"
# DIQQAT: Bu yerga o'zingizni LIVE TOKENingizni qo'yasiz (hozircha test turaversin)
PAYMENT_TOKEN = "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"

ADMIN_ID = 6651261925 
FREE_LIMIT = 5 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
engine = HalolScannerEngine(INGREDIENTS_DB)

# Bazani ishga tushiramiz
db.init_db()

# --- MENU ---
def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📸 Skanerlash"), types.KeyboardButton(text="👤 Profil"))
    builder.row(types.KeyboardButton(text="💎 Premium (9000 so'm)"), types.KeyboardButton(text="📊 Statistika"))
    return builder.as_markup(resize_keyboard=True)

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    db.register_user(user_id) # Bazaga yozib qo'yamiz
    await message.answer(
        f"👋 **Assalomu alaykum!**\nSizda kunlik **{FREE_LIMIT} ta** bepul tekshirish imkoniyati bor.", 
        reply_markup=get_main_menu(), 
        parse_mode="Markdown"
    )

# --- ADMIN PANEL ---
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    users, premiums, scans = db.get_stats() # Bazadan olamiz

    text = (
        f"👨‍💻 **ADMIN PANEL** (Baza ulangan 🗄)\n"
        f"▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👥 Jami foydalanuvchilar: **{users}** ta\n"
        f"💎 Premium olganlar: **{premiums}** ta\n"
        f"📸 Jami skanerlar: **{scans}** ta\n"
    )
    await message.answer(text, parse_mode="Markdown")

# --- PROFIL ---
@dp.message(F.text == "👤 Profil")
async def btn_profile(message: types.Message):
    user_id = message.from_user.id
    stats = db.get_user_stats(user_id) # (total, is_premium, today)
    
    if not stats:
        db.register_user(user_id)
        stats = (0, 0, 0)
        
    total_scans, is_prem, today_scans = stats
    name = message.from_user.full_name

    if is_prem:
        status_header = "💎 PREMIUM STATUS"
        limit_visual = "♾ Cheksiz"
        desc = "✅ Sizda cheklovlar yo'q!"
    else:
        status_header = "👤 ODDIY FOYDALANUVCHI"
        left = max(0, FREE_LIMIT - today_scans)
        bar = "▰" * today_scans + "▱" * left
        limit_visual = f"{bar} ({left} ta qoldi)"
        desc = f"🔒 Kunlik limit: {FREE_LIMIT} ta"

    text = (
        f"📂 **FOYDALANUVCHI PROFILI**\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👤 **Ism:** {name}\n"
        f"🆔 **ID:** `{user_id}`\n\n"
        f"📊 **STATISTIKA**\n"
        f"• Bugungi urinishlar: **{today_scans}** ta\n"
        f"• Jami skanerlar: **{total_scans}** ta\n\n"
        f"💳 **OBUNA HOLATI**\n"
        f"• Status: **{status_header}**\n"
        f"• Limit: {limit_visual}\n\n"
        f"💡 _{desc}_"
    )
    await message.answer(text, parse_mode="Markdown")

# --- STATISTIKA ---
@dp.message(F.text == "📊 Statistika")
async def btn_stats(message: types.Message):
    stats = db.get_user_stats(message.from_user.id)
    count = stats[0] if stats else 0
    await message.answer(f"📊 Jami tekshiruvlaringiz: **{count}** ta")

# --- TO'LOV (PREMIUM) ---
@dp.message(F.text.contains("Premium"))
async def buy_premium(message: types.Message):
    if db.is_premium(message.from_user.id):
        await message.answer("Siz allaqachon Premiumdasiz! ✅")
        return
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Premium Obuna (Cheksiz)",
        description="Cheksiz skanerlash va Reklamasiz rejim.",
        payload="click_sub_limit",
        provider_token=PAYMENT_TOKEN,
        currency="UZS",
        prices=[types.LabeledPrice(label="Obuna narxi", amount=900000)], 
        start_parameter="buy_premium",
        is_flexible=False
    )

@dp.pre_checkout_query()
async def checkout(q): await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(F.successful_payment)
async def got_payment(message: types.Message):
    user_id = message.from_user.id
    db.set_premium(user_id) # <--- Bazaga yozamiz: "Bu odam pul to'ladi"
    await message.answer("🎉 **To'lov qabul qilindi!**\nSiz endi PREMIUM foydalanuvchisiz. Cheksiz ishlating!")

# --- YORDAMCHILAR ---
def get_status_emoji(status):
    if status == "HAROM": return "🔴"
    if status == "SHUBHALI": return "🟡"
    if status == "ZARARLI": return "🟠"
    return "🟢"

# --- 🔥 RASM QABUL QILISH ---
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    
    # 1. Limit tekshirish (Bazadan)
    if db.check_limit(user_id, FREE_LIMIT):
        await message.answer("⛔️ **Kunlik limit tugadi!**\nErtaga qaytib keling yoki Premium oling.")
        return

    msg = await message.answer("⏳ Rasm o'qilmoqda...")
    temp_filename = f"temp_{user_id}.jpg"
    
    try:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        await bot.download_file(file.file_path, temp_filename)
        
        # 2. Hisobni oshirish (Bazaga +1 yozamiz)
        db.add_scan(user_id)
        
        scanned_text = pytesseract.image_to_string(Image.open(temp_filename))
        result = engine.check_text(scanned_text)
        
        if result['status'] == "ERROR":
             response = f"⚠️ {result['message']}"
        elif result['status'] == "GREEN":
            response = "🟢 **Xavfli kodlar topilmadi**"
        else:
            response = f"{result['message']}\n\n"
            if "details" in result:
                for item in result["details"]:
                    ing = item['ingredient']
                    icon = get_status_emoji(ing.status)
                    ing_name = ing.names[1].title() if len(ing.names) > 1 else ing.names[0]
                    response += f"{icon} **{ing.code}** ({ing_name}) - {ing.status}\n"

        clean_text = scanned_text.strip()
        if len(clean_text) < 5:
            preview_text = "⚠️ (Rasmda matn aniqlanmadi)."
        else:
            preview_text = clean_text[:300] + "..." if len(clean_text) > 300 else clean_text

        final_msg = f"{response}\n\n📝 **Bot o'qigan matn:**\n_{preview_text}_"

        if os.path.exists(temp_filename): os.remove(temp_filename)
        await msg.delete()
        await message.answer(final_msg, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"Xatolik: {e}")
        if os.path.exists(temp_filename): os.remove(temp_filename)

# --- 🔥 MATN QABUL QILISH ---
@dp.message(F.text)
async def main_logic(message: types.Message):
    text = message.text.lower()
    if len(text) < 3 or "salom" in text:
        await message.answer("Mahsulot tarkibini yozing yoki rasmga oling.")
        return

    user_id = message.from_user.id
    
    if db.check_limit(user_id, FREE_LIMIT):
        await message.answer("⛔️ **Limit tugadi!** Premium oling.")
        return

    db.add_scan(user_id) # Bazaga yozamiz

    result = engine.check_text(message.text)
    if result['status'] == "GREEN":
        resp = "🟢 **Xavfli kodlar topilmadi**"
    else:
        resp = f"{result['message']}\n\n"
        for item in result.get("details", []):
            ing = item['ingredient']
            icon = get_status_emoji(ing.status)
            ing_name = ing.names[1].title() if len(ing.names) > 1 else ing.names[0]
            resp += f"{icon} **{ing.code}** ({ing_name}) - {ing.status}\n"
            
    await message.answer(resp, parse_mode="Markdown")

async def main():
    print("Bot ishga tushdi... Baza: SQLite (/app/data)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
