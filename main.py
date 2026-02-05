import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from brain import HalolScannerEngine, INGREDIENTS_DB
from PIL import Image
import pytesseract

# --- ⚠️ SOZLAMALAR ---
# Tokenlar
BOT_TOKEN = "8555323979:AAF41Dc67DbyH1Rpcj6n3PeubPInoFxISmk"
PAYMENT_TOKEN = "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"

# 🛑 SIZNING ADMIN ID RAQAMINGIZ
ADMIN_ID = 6651261925 

FREE_LIMIT = 5 # Bepul limit soni

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
engine = HalolScannerEngine(INGREDIENTS_DB)

# 💾 XOTIRA
PREMIUM_USERS = []
USER_SCANS = {} 
ALL_USERS = set() 

# --- MENU TUGMALARI ---
def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📸 Skanerlash"), types.KeyboardButton(text="👤 Profil"))
    builder.row(types.KeyboardButton(text="💎 Premium (9000 so'm)"), types.KeyboardButton(text="📊 Statistika"))
    return builder.as_markup(resize_keyboard=True)

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    ALL_USERS.add(user_id) 
    await message.answer(
        f"👋 **Assalomu alaykum!**\nSizda kunlik **{FREE_LIMIT} ta** bepul tekshirish imkoniyati bor.", 
        reply_markup=get_main_menu(), 
        parse_mode="Markdown"
    )

# --- 🕵️‍♂️ ADMIN PANEL ---
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    total_users = len(ALL_USERS)
    premium_count = len(PREMIUM_USERS)
    active_scans = sum(USER_SCANS.values())

    text = (
        f"👨‍💻 **ADMIN PANEL**\n"
        f"▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👥 Jami foydalanuvchilar: **{total_users}** ta\n"
        f"💎 Premium olganlar: **{premium_count}** ta\n"
        f"📸 Jami qilingan skanerlar: **{active_scans}** ta\n\n"
        f"✅ Server va Tesseract ishlamoqda!"
    )
    await message.answer(text, parse_mode="Markdown")

# --- PROFIL ---
@dp.message(F.text == "👤 Profil")
async def btn_profile(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.full_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    count = USER_SCANS.get(user_id, 0)
    
    if user_id in PREMIUM_USERS:
        status_header = "💎 PREMIUM STATUS"
        limit_visual = "♾ Cheksiz"
        desc = "✅ Sizda cheklovlar yo'q!"
    else:
        status_header = "👤 ODDIY FOYDALANUVCHI"
        used = min(count, FREE_LIMIT)
        left = max(0, FREE_LIMIT - count)
        bar = "▰" * used + "▱" * left
        limit_visual = f"{bar} ({left} ta qoldi)"
        desc = f"🔒 Kunlik limit: {FREE_LIMIT} ta"

    text = (
        f"📂 **FOYDALANUVCHI PROFILI**\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👤 **Ism:** {name}\n"
        f"🌐 **Username:** {username}\n"
        f"🆔 **ID:** `{user_id}`\n\n"
        f"📊 **STATISTIKA**\n"
        f"• Skanerlar: **{count}** ta\n\n"
        f"💳 **OBUNA HOLATI**\n"
        f"• Status: **{status_header}**\n"
        f"• Limit: {limit_visual}\n\n"
        f"💡 _{desc}_"
    )
    await message.answer(text, parse_mode="Markdown")

# --- STATISTIKA ---
@dp.message(F.text == "📊 Statistika")
async def btn_stats(message: types.Message):
    count = USER_SCANS.get(message.from_user.id, 0)
    await message.answer(f"📊 Jami tekshiruvlar: **{count}** ta")

# --- SKANERLASH INFO ---
@dp.message(F.text == "📸 Skanerlash")
async def btn_scan_info(message: types.Message):
    await message.answer("📸 Mahsulot tarkibini rasmga olib yuboring yoki kodni yozing (masalan: E120).")

# --- TO'LOV (PREMIUM) ---
@dp.message(F.text.contains("Premium"))
async def buy_premium(message: types.Message):
    if message.from_user.id in PREMIUM_USERS:
        await message.answer("Siz allaqachon Premiumdasiz! ✅")
        return
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Premium Obuna (1 oy)",
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
    if message.from_user.id not in PREMIUM_USERS:
        PREMIUM_USERS.append(message.from_user.id)
    await message.answer("🎉 **To'lov qabul qilindi!**\nLimitingiz olib tashlandi. Cheksiz foydalaning!")

# --- YORDAMCHI FUNKSIYALAR ---
def check_limit_reached(user_id: int) -> bool:
    if user_id in PREMIUM_USERS:
        return False
    count = USER_SCANS.get(user_id, 0)
    return count >= FREE_LIMIT

def get_status_emoji(status):
    if status == "HAROM": return "🔴"
    if status == "SHUBHALI": return "🟡"
    if status == "ZARARLI": return "🟠"
    return "🟢"

# --- 🔥 RASM QABUL QILISH (YANGILANGAN) ---
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    ALL_USERS.add(user_id) 

    if check_limit_reached(user_id):
        await message.answer("⛔️ **Limit tugadi!** Davom ettirish uchun Premium oling.")
        return

    msg = await message.answer("⏳ Rasm o'qilmoqda...")
    temp_filename = f"temp_{user_id}.jpg"
    
    try:
        # 1. Rasmni yuklab olamiz
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        await bot.download_file(file.file_path, temp_filename)
        
        # 2. Hisobni oshiramiz
        USER_SCANS[user_id] = USER_SCANS.get(user_id, 0) + 1
        
        # 3. MATNNI O'QISH (O'zimiz o'qiymiz)
        scanned_text = pytesseract.image_to_string(Image.open(temp_filename))
        
        # 4. TEKSHIRISH
        result = engine.check_text(scanned_text)
        
        # 5. JAVOB TAYYORLASH
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

        # 🔍 ISHONCH UCHUN: Bot o'qigan matnni ko'rsatamiz
        # Agar matn bo'sh bo'lsa yoki juda qisqa bo'lsa
        clean_text = scanned_text.strip()
        if len(clean_text) < 5:
            preview_text = "⚠️ (Rasmda matn aniqlanmadi. Iltimos, tiniqroq rasm yuboring)."
        else:
            preview_text = clean_text[:300] + "..." if len(clean_text) > 300 else clean_text

        final_msg = f"{response}\n\n📝 **Bot o'qigan matn parchasi:**\n_{preview_text}_"

        if os.path.exists(temp_filename): os.remove(temp_filename)
        await msg.delete()
        await message.answer(final_msg, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")
        if os.path.exists(temp_filename): os.remove(temp_filename)

# --- 🔥 MATN QABUL QILISH ---
@dp.message(F.text)
async def main_logic(message: types.Message):
    text = message.text.lower()
    if len(text) < 3 or "salom" in text:
        await message.answer("Mahsulot tarkibini yozing yoki rasmga oling.")
        return

    user_id = message.from_user.id
    ALL_USERS.add(user_id)

    if check_limit_reached(user_id):
        await message.answer("⛔️ **Limit tugadi!** Premium oling.")
        return

    USER_SCANS[user_id] = USER_SCANS.get(user_id, 0) + 1
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
    print("Bot (ID 6651261925) ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
