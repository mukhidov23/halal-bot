import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import brain  # <--- Yangi AI miyani ulaymiz
import db     # <--- Baza fayli joyida qoladi

# --- ⚠️ SOZLAMALAR ---
# Bu yerga o'z Tokeningizni qo'yasiz
BOT_TOKEN = "8555323979:AAF41Dc67DbyH1Rpcj6n3PeubPInoFxISmk" 
PAYMENT_TOKEN = "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"

ADMIN_ID = 6651261925 
FREE_LIMIT = 5 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Bazani ishga tushiramiz
db.init_db()

# --- MENU TUGMALARI ---
def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📸 Skanerlash"), types.KeyboardButton(text="👤 Profil"))
    builder.row(types.KeyboardButton(text="💎 Premium (10 000 so'm)"), types.KeyboardButton(text="📊 Statistika"))
    return builder.as_markup(resize_keyboard=True)

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    db.register_user(user_id) 
    await message.answer(
        f"👋 **Assalomu alaykum!**\nSizda kunlik **{FREE_LIMIT} ta** bepul AI tekshiruvi bor.", 
        reply_markup=get_main_menu(), 
        parse_mode="Markdown"
    )

# --- ADMIN PANEL ---
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    users, premiums, scans = db.get_stats()
    text = (
        f"👨‍💻 **ADMIN PANEL**\n▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👥 Foydalanuvchilar: **{users}**\n💎 Premium: **{premiums}**\n📸 Skanerlar: **{scans}**"
    )
    await message.answer(text, parse_mode="Markdown")

# --- SKANERLASH INFO ---
@dp.message(F.text == "📸 Skanerlash")
async def btn_scan_info(message: types.Message):
    await message.answer("📸 Mahsulotning **tarkibi yozilgan joyini** rasmga olib yuboring.\nMen uni Sun'iy Intellekt yordamida o'qib chiqaman.")

# --- PROFIL ---
@dp.message(F.text == "👤 Profil")
async def btn_profile(message: types.Message):
    user_id = message.from_user.id
    stats = db.get_user_stats(user_id)
    if not stats: stats = (0, 0, 0)
    total, is_prem, today = stats

    if is_prem:
        limit_txt = "♾ Cheksiz (Premium)"
    else:
        limit_txt = f"{FREE_LIMIT - today} ta qoldi"

    text = f"👤 **PROFIL**\n🆔 `{user_id}`\n📊 Jami: {total} ta\n📅 Bugun: {today} ta\n🔒 Limit: {limit_txt}"
    await message.answer(text, parse_mode="Markdown")

# --- STATISTIKA ---
@dp.message(F.text == "📊 Statistika")
async def btn_stats(message: types.Message):
    stats = db.get_user_stats(message.from_user.id)
    count = stats[0] if stats else 0
    await message.answer(f"📊 Siz jami **{count}** ta mahsulotni AI orqali tekshirdingiz.")

# --- PREMIUM OLISH ---
@dp.message(F.text.contains("Premium"))
async def buy_premium(message: types.Message):
    if db.is_premium(message.from_user.id):
        await message.answer("Siz allaqachon Premiumdasiz! ✅")
        return
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Premium Obuna (Cheksiz)",
        description="Cheksiz AI skanerlash.",
        payload="click_sub_ai",
        provider_token=PAYMENT_TOKEN,
        currency="UZS",
        prices=[types.LabeledPrice(label="Obuna narxi", amount=1000000)], 
        start_parameter="buy_premium",
        is_flexible=False
    )

@dp.pre_checkout_query()
async def checkout(q): await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(F.successful_payment)
async def got_payment(message: types.Message):
    db.set_premium(message.from_user.id) 
    await message.answer("🎉 **To'lov qabul qilindi!** Premium faollashdi.")

# --- 🔥 AI BILAN RASM TEKSHIRISH ---
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    if db.check_limit(user_id, FREE_LIMIT):
        await message.answer("⛔️ **Limit tugadi!** Ertaga keling yoki Premium oling.")
        return

    wait_msg = await message.answer("🧠 **Sun'iy Intellekt o'qimoqda...**\n(Bu 3-5 soniya vaqt oladi)")
    
    # Rasmni yuklab olamiz
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = f"temp_{user_id}.jpg"
    await bot.download_file(file.file_path, file_path)

    # Bazaga yozamiz
    db.add_scan(user_id)

    # AI ga yuboramiz
    try:
        ai_response = brain.analyze_image_with_ai(file_path)
        await wait_msg.delete()
        await message.answer(ai_response, parse_mode="Markdown")
    except Exception as e:
        await wait_msg.delete()
        await message.answer(f"Xatolik: {e}")
    finally:
        if os.path.exists(file_path): os.remove(file_path)

# --- 🔥 AI BILAN MATN TEKSHIRISH ---
@dp.message(F.text)
async def handle_text(message: types.Message):
    text = message.text
    # Qisqa so'zlarni va buyruqlarni o'tkazib yuboramiz
    if len(text) < 4 or text.lower() in ["/start", "salom", "start"]: return

    user_id = message.from_user.id
    if db.check_limit(user_id, FREE_LIMIT):
        await message.answer("⛔️ **Limit tugadi!** Premium oling.")
        return

    wait_msg = await message.answer("🧠 **Tahlil qilinmoqda...**")
    db.add_scan(user_id)
    
    response = brain.analyze_text_with_ai(text)
    
    await wait_msg.delete()
    await message.answer(response, parse_mode="Markdown")

async def main():
    print("Bot ishga tushdi (Gemini AI Powered) 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
