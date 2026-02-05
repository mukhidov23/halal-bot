import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from brain import HalolScannerEngine, INGREDIENTS_DB

# --- ⚠️ TOKENLAR ---
BOT_TOKEN = "8555323979:AAF41Dc67DbyH1Rpcj6n3PeubPInoFxISmk"
PAYMENT_TOKEN = "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"

# --- SOZLAMALAR ---
FREE_LIMIT = 5

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
engine = HalolScannerEngine(INGREDIENTS_DB)

# 💾 XOTIRA
PREMIUM_USERS = []
USER_SCANS = {}

# --- MENU ---
def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📸 Skanerlash"), types.KeyboardButton(text="👤 Profil"))
    builder.row(types.KeyboardButton(text="💎 Premium (9000 so'm)"), types.KeyboardButton(text="📊 Statistika"))
    return builder.as_markup(resize_keyboard=True)

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"👋 **Assalomu alaykum!**\nSizda {FREE_LIMIT} ta bepul limit bor.", reply_markup=get_main_menu(), parse_mode="Markdown")

# --- 🔥 YANGILANGAN PROFIL (PRO DIZAYN) ---
@dp.message(F.text == "👤 Profil")
async def btn_profile(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.full_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    
    # Statistika olish
    count = USER_SCANS.get(user_id, 0)
    
    # Premium tekshirish va Dizayn
    if user_id in PREMIUM_USERS:
        status_header = "💎 PREMIUM STATUS"
        limit_visual = "♾ Cheksiz"
        desc = "✅ Sizda hech qanday cheklovlar yo'q!"
    else:
        status_header = "👤 ODDIY FOYDALANUVCHI"
        # Progress Bar yasash (Masalan: 🟥🟥⬜️⬜️⬜️)
        used = min(count, FREE_LIMIT)
        left = max(0, FREE_LIMIT - count)
        
        # Vizual shkala
        bar = "▰" * used + "▱" * left
        limit_visual = f"{bar} ({left} ta qoldi)"
        desc = f"🔒 Kunlik limit: {FREE_LIMIT} ta"

    # Chiroyli Javob Matni
    text = (
        f"📂 **FOYDALANUVCHI PROFILI**\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👤 **Ism:** {name}\n"
        f"🌐 **Username:** {username}\n"
        f"🆔 **ID:** `{user_id}`\n\n"
        
        f"📊 **STATISTIKA**\n"
        f"• Jami skanerlar: **{count}** ta\n\n"
        
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
    await message.answer("📸 Mahsulot tarkibini rasmga olib yuboring.")

# --- TO'LOV ---
@dp.message(F.text.contains("Premium"))
async def buy_premium(message: types.Message):
    if message.from_user.id in PREMIUM_USERS:
        await message.answer("Siz allaqachon Premiumdasiz!")
        return
    await bot.send_invoice(
        chat_id=message.chat.id, title="Premium Obuna", description="Cheksiz rejim.", payload="click_sub",
        provider_token=PAYMENT_TOKEN, currency="UZS", prices=[types.LabeledPrice(label="Obuna", amount=900000)],
        start_parameter="buy", is_flexible=False
    )

@dp.pre_checkout_query()
async def checkout(q): await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(F.successful_payment)
async def got_payment(message: types.Message):
    if message.from_user.id not in PREMIUM_USERS: PREMIUM_USERS.append(message.from_user.id)
    await message.answer("🎉 To'lov qabul qilindi! Premium faollashdi.")

# --- YORDAMCHI FUNKSIYALAR ---
def check_limit_reached(user_id):
    if user_id in PREMIUM_USERS: return False
    return USER_SCANS.get(user_id, 0) >= FREE_LIMIT

def get_status_emoji(status):
    if status == "HAROM": return "🔴"
    if status == "SHUBHALI": return "🟡"
    if status == "ZARARLI": return "🟠"
    return "🟢"

# --- 🔥 1. RASM QABUL QILISH ---
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    if check_limit_reached(user_id):
        await message.answer("⛔️ Limit tugadi! Premium oling.")
        return

    msg = await message.answer("⏳ Rasm o'qilmoqda...")
    try:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        temp_filename = f"temp_{user_id}.jpg"
        await bot.download_file(file.file_path, temp_filename)
        
        USER_SCANS[user_id] = USER_SCANS.get(user_id, 0) + 1
        result = engine.scan_image(temp_filename)
        
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

        if os.path.exists(temp_filename): os.remove(temp_filename)
        await msg.delete()
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Xatolik: {e}")

# --- 🔥 2. MATN QABUL QILISH ---
@dp.message(F.text)
async def main_logic(message: types.Message):
    if len(message.text) < 3 or "salom" in message.text.lower():
        await message.answer("Tarkibni yozing.")
        return
    
    user_id = message.from_user.id
    if check_limit_reached(user_id):
        await message.answer("⛔️ Limit tugadi!")
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
    print("Bot PRO Profil bilan ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
