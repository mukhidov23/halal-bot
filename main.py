import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import brain  # <--- MIYA (Tahlil va Reklama shu yerda)
import db     # <--- BAZA (Foydalanuvchilar va Limitlar)

# --- ⚠️ SOZLAMALAR ---
BOT_TOKEN = "8555323979:AAF41Dc67DbyH1Rpcj6n3PeubPInoFxISmk"
PAYMENT_TOKEN = "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"

# --- 👑 SIZNING ID RAQAMINGIZ ---
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

# --- START BUYRUG'I ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    db.register_user(user_id) 
    await message.answer(
        f"👋 **Assalomu alaykum!**\nSizda kunlik {FREE_LIMIT} ta bepul AI tekshiruvi bor.\n\n"
        f"Mahsulot tarkibini yozing yoki rasmga olib yuboring.", 
        reply_markup=get_main_menu()
    )

# --- ADMIN PANEL (Statistika + Broadcast) ---
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    users, premiums, scans = db.get_stats()
    text = (
        f"👨‍💻 **ADMIN PANEL**\n"
        f"▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👥 Jami foydalanuvchilar: {users}\n"
        f"💎 Premium olganlar: {premiums}\n"
        f"📸 Jami skanerlar: {scans}\n\n"
        f"📢 **Xabar tarqatish:**\n`/send Xabar matni` ko'rinishida yozing."
    )
    await message.answer(text, parse_mode="Markdown")

# --- 🔥 REKLAMA TARQATISH (BROADCAST) ---
@dp.message(Command("send"))
async def cmd_send_all(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID: return

    text = command.args
    if not text:
        await message.answer("⚠️ Xabar matni yo'q! Namuna: `/send Yangi chegirmalar!`")
        return

    users = db.get_all_users()
    await message.answer(f"📢 Xabar {len(users)} ta odamga yuborilmoqda...")

    sent = 0
    blocked = 0

    for user_id in users:
        try:
            # HTML formati orqali chiroyli xabar
            await bot.send_message(user_id, f"<b>📢 ADMIN XABARI:</b>\n\n{text}", parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05) 
        except:
            blocked += 1
    
    await message.answer(
        f"✅ **TARQATISH TUGADI!**\n\n"
        f"📨 Yetib bordi: {sent} ta\n"
        f"🚫 Bloklangan/O'chirilgan: {blocked} ta"
    )

# --- 👤 PROFIL ---
@dp.message(F.text == "👤 Profil")
async def btn_profile(message: types.Message):
    user_id = message.from_user.id
    stats = db.get_user_stats(user_id)
    if not stats: stats = (0, 0, 0)
    total_scans, is_prem, today_scans = stats
    
    status_txt = "💎 PREMIUM (Cheksiz)" if is_prem else f"👤 ODDIY (Limit: {FREE_LIMIT})"
    left = max(0, FREE_LIMIT - today_scans) if not is_prem else "♾"
    
    text = (
        f"👤 **Foydalanuvchi:** {message.from_user.full_name}\n"
        f"🆔 **ID:** {user_id}\n\n"
        f"📊 Jami tekshiruvlar: {total_scans}\n"
        f"💳 Status: {status_txt}\n"
        f"🔒 Bugungi qolgan limit: {left}"
    )
    await message.answer(text)

# --- 📊 STATISTIKA ---
@dp.message(F.text == "📊 Statistika")
async def btn_stats(message: types.Message):
    stats = db.get_user_stats(message.from_user.id)
    count = stats[0] if stats else 0
    await message.answer(f"📊 Siz shu vaqtgacha jami **{count}** ta mahsulotni tekshirdingiz.")

# --- 📸 SKANERLASH INFO ---
@dp.message(F.text == "📸 Skanerlash")
async def btn_scan_info(message: types.Message):
    await message.answer("📸 Mahsulotning **tarkibi yozilgan joyini** rasmga olib yuboring.\nMen uni o'qib, tahlil qilib beraman.")

# --- 💎 PREMIUM SOTIB OLISH ---
@dp.message(F.text.contains("Premium"))
async def buy_premium(message: types.Message):
    if db.is_premium(message.from_user.id):
        await message.answer("✅ Sizda allaqachon Premium bor!")
        return
    
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Premium Obuna (Cheksiz)",
        description="Kunlik limitni olib tashlash va cheksiz skanerlash.",
        payload="click_sub_ai",
        provider_token=PAYMENT_TOKEN,
        currency="UZS",
        prices=[types.LabeledPrice(label="Bir martalik to'lov", amount=1000000)], # 10 000 so'm
        start_parameter="buy_premium",
        is_flexible=False
    )

@dp.pre_checkout_query()
async def checkout(q): 
    await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(F.successful_payment)
async def got_payment(message: types.Message):
    db.set_premium(message.from_user.id) 
    await message.answer("🎉 **Tabriklaymiz!** To'lov muvaffaqiyatli amalga oshirildi.\nEndi sizda cheklovlar yo'q! ✅")

# --- 👮‍♂️ ADMINGA XABAR BERISH ---
async def notify_admin_missing_codes(codes, user_text):
    if not codes: return
    msg = (
        f"👨‍💻 **ADMIN DIQQATIGA!**\n"
        f"Foydalanuvchi bazada yo'q kodlarni qidirdi.\n\n"
        f"🆔 Kodlar: **{', '.join(codes)}**\n"
        f"📝 Matn: _{user_text[:100]}..._"
    )
    try: await bot.send_message(ADMIN_ID, msg)
    except: pass

# --- 🖼 RASM TEKSHIRISH ---
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    if db.check_limit(user_id, FREE_LIMIT):
        await message.answer("⛔️ **Kunlik limit tugadi!**\nErtaga keling yoki Premium sotib oling.")
        return

    wait_msg = await message.answer("⏳ **Rasm o'qilmoqda...**")
    
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = f"temp_{user_id}.jpg"
    await bot.download_file(file.file_path, file_path)
    
    db.add_scan(user_id)

    try:
        response_text, missing_codes = brain.analyze_image_with_ai(file_path)
        await wait_msg.delete()
        await message.answer(response_text) # Reklama shu yerda chiqadi (brain.py dan keladi)
        
        if missing_codes: 
            await notify_admin_missing_codes(missing_codes, "Rasm orqali")
            
    except Exception as e:
        await wait_msg.delete()
        await message.answer(f"⚠️ Xatolik yuz berdi: {e}")
    finally:
        if os.path.exists(file_path): os.remove(file_path)

# --- 📝 MATN TEKSHIRISH ---
@dp.message(F.text)
async def handle_text(message: types.Message):
    text = message.text
    # Qisqa so'zlar yoki buyruqlarni o'tkazib yuboramiz
    if len(text) < 3 or text.startswith("/"): return

    user_id = message.from_user.id
    if db.check_limit(user_id, FREE_LIMIT):
        await message.answer("⛔️ **Kunlik limit tugadi!**\nPremium oling.")
        return

    wait_msg = await message.answer("⏳ **Tahlil qilinmoqda...**")
    db.add_scan(user_id)
    
    response_text, missing_codes = brain.analyze_text_with_ai(text)
    
    await wait_msg.delete()
    await message.answer(response_text) # Reklama shu yerda chiqadi
    
    if missing_codes: 
        await notify_admin_missing_codes(missing_codes, text)

# --- 🚀 ISHGA TUSHIRISH ---
async def main():
    print("Bot muvaffaqiyatli ishga tushdi! 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
