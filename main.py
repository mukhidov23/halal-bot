import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import brain
import db

# --- ⚠️ SOZLAMALAR ---
BOT_TOKEN = "8555323979:AAF41Dc67DbyH1Rpcj6n3PeubPInoFxISmk"
PAYMENT_TOKEN = "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"
ADMIN_ID = 6651261925 
FREE_LIMIT = 3 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db.init_db()

# --- MENU ---
def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📸 Skanerlash"), types.KeyboardButton(text="👤 Profil"))
    builder.row(types.KeyboardButton(text="💎 Premium (10 000 so'm)"), types.KeyboardButton(text="📊 Statistika"))
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    db.register_user(user_id) 
    await message.answer(
        f"👋 **Assalomu alaykum, {message.from_user.first_name}!**\n\n"
        f"Men mahsulotlarni Halol yoki Haromligini aniqlovchi aqlli botman.\n"
        f"📸 Rasm yuboring yoki tarkibini yozing.", 
        reply_markup=get_main_menu()
    )

# --- 🔥 ADMIN PANEL (Siz xohlagan dizayn) ---
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    users, premiums, scans = db.get_stats()
    text = (
        f"👨‍💻 ADMIN PANEL\n"
        f"▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👥 Foydalanuvchilar: {users}\n"
        f"💎 Premium: {premiums}\n"
        f"📸 Skanerlar: {scans}\n\n"
        f"📢 Xabar tarqatish:\n`/send Xabar matni`"
    )
    await message.answer(text) # Markdown shart emas, oddiy matn chiroyli chiqadi

@dp.message(Command("send"))
async def cmd_send_all(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID: return
    text = command.args
    if not text: return await message.answer("⚠️ Matn yo'q!")
    
    users = db.get_all_users()
    await message.answer(f"🚀 Xabar {len(users)} kishiga ketmoqda...")
    
    sent = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, f"<b>🔔 ADMIN XABARI:</b>\n\n{text}", parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)
        except: pass
    
    await message.answer(f"✅ **Yuborildi:** {sent} ta")

# --- 👤 PROFIL (Siz xohlagan "Papka" dizayni) ---
@dp.message(F.text.contains("Profil"))
async def btn_profile(message: types.Message):
    user_id = message.from_user.id
    stats = db.get_user_stats(user_id)
    if not stats: stats = (0, 0, 0)
    total, is_prem, today = stats
    
    name = message.from_user.full_name

    if is_prem:
        status_header = "💎 PREMIUM STATUS"
        limit_visual = "♾ Cheksiz"
        desc = "✅ Sizda cheklovlar yo'q!"
    else:
        status_header = "👤 ODDIY FOYDALANUVCHI"
        # Progress Bar: ▰▰▰▱▱
        limit = FREE_LIMIT
        used = min(today, limit)
        left = limit - used
        # 10 ta katakchadan iborat vizual
        filled_count = int((used / limit) * 10)
        bar = "▰" * filled_count + "▱" * (10 - filled_count)
        
        limit_visual = f"{bar} ({left} ta qoldi)"
        desc = f"🔒 Kunlik limit: {limit} ta"

    text = (
        f"📂 FOYDALANUVCHI PROFILI\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👤 Ism: {name}\n"
        f"🆔 ID: {user_id}\n\n"
        f"📊 STATISTIKA\n"
        f"• Bugun: {today} ta\n"
        f"• Jami: {total} ta\n\n"
        f"💳 OBUNA HOLATI\n"
        f"• Status: {status_header}\n"
        f"• Limit: {limit_visual}\n\n"
        f"💡 {desc}"
    )
    await message.answer(text)

# --- 📊 STATISTIKA (Kengaytirilgan) ---
@dp.message(F.text.contains("Statistika"))
async def btn_stats(message: types.Message):
    stats = db.get_user_stats(message.from_user.id)
    if not stats: stats = (0, 0, 0)
    total, is_prem, today = stats
    
    text = (
        f"📊 **SHAXSIY STATISTIKA**\n"
        f"▬▬▬▬▬▬▬▬▬▬▬\n"
        f"📅 **Bugungi tahlillar:** {today} ta\n"
        f"🗂 **Jami tahlillar:** {total} ta\n\n"
        f"🍏 Biz bilan halol yeng!"
    )
    await message.answer(text, parse_mode="Markdown")

# --- SKANERLASH INFO ---
@dp.message(F.text.contains("Skanerlash"))
async def btn_scan_info(message: types.Message):
    await message.answer(
        "📸 **Skanerlash rejimi**\n\n"
        "Mahsulotning **tarkibi yozilgan joyini** (Ingredientlar) rasmga olib yuboring.\n"
        "Yoki kodlarni qo'lda yozing (masalan: E120)."
    )

# --- PREMIUM SOTIB OLISH ---
@dp.message(F.text.contains("Premium"))
async def buy_premium(message: types.Message):
    if db.is_premium(message.from_user.id):
        await message.answer("✅ Siz allaqachon Premiumdasiz!")
        return
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Premium Obuna",
        description="Cheksiz foydalanish huquqi.",
        payload="click_sub_ai",
        provider_token=PAYMENT_TOKEN,
        currency="UZS",
        prices=[types.LabeledPrice(label="Premium", amount=1000000)],
        start_parameter="buy_premium",
        is_flexible=False
    )

@dp.pre_checkout_query()
async def checkout(q): await bot.answer_pre_checkout_query(q.id, ok=True)
@dp.message(F.successful_payment)
async def got_payment(message: types.Message):
    db.set_premium(message.from_user.id) 
    await message.answer("🎉 **Tabriklaymiz!** Premium faollashdi! ✅")

async def notify_admin(codes, text):
    if not codes: return
    try: await bot.send_message(ADMIN_ID, f"⚠️ **Yangi kodlar:** {', '.join(codes)}\n📝 {text[:50]}...")
    except: pass

# --- RASM VA MATN HANDLERLARI ---
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    if db.check_limit(user_id, FREE_LIMIT):
        return await message.answer("⛔️ **Limit tugadi!** Premium oling.")
    
    msg = await message.answer("⏳ **Rasm o'qilmoqda...**")
    path = f"temp_{user_id}.jpg"
    await bot.download(message.photo[-1], destination=path)
    db.add_scan(user_id)
    
    try:
        res, codes = brain.analyze_image_with_ai(path)
        await msg.delete()
        await message.answer(res)
        if codes: await notify_admin(codes, "Rasm")
    except Exception as e:
        await msg.delete()
        await message.answer(f"Xato: {e}")
    finally:
        if os.path.exists(path): os.remove(path)

@dp.message(F.text)
async def handle_text(message: types.Message):
    text = message.text
    
    # 🛑 TUZATISH: Tugmalar bosilganda tahlil qilmaslik uchun to'siq
    if text in ["📸 Skanerlash", "👤 Profil", "💎 Premium (10 000 so'm)", "📊 Statistika"]:
        return 

    if len(text) < 3 or text.startswith("/"): return
    
    user_id = message.from_user.id
    if db.check_limit(user_id, FREE_LIMIT):
        return await message.answer("⛔️ **Limit tugadi!**")
    
    msg = await message.answer("⏳ **Tahlil...**")
    db.add_scan(user_id)
    
    res, codes = brain.analyze_text_with_ai(text)
    
    await msg.delete()
    await message.answer(res)
    if codes: await notify_admin(codes, text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
