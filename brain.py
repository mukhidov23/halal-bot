import google.generativeai as genai
import os
from PIL import Image

# --- 🔑 SIZNING KALITINGIZ ---
API_KEY = "AIzaSyC5QZ-GMyg30wmCEmlHO0g2NW4JZiQD2ms"

# Googleni sozlaymiz
genai.configure(api_key=API_KEY)

# --- 🔥 TUZATISH SHU YERDA ---
# Biz eng ishonchli 'gemini-1.5-pro' modelini ishlatamiz.
# Agar u ham topilmasa, avtomatik 'gemini-pro' (eski versiya) ga o'tadi.
def get_model():
    try:
        return genai.GenerativeModel('gemini-1.5-pro')
    except:
        return genai.GenerativeModel('gemini-pro')

model = get_model()

# --- 🧠 BOTNING MIYASI ---
SYSTEM_PROMPT = """
Sen professional oziq-ovqat texnologi va Islomiy halol standarti ekspertisan.
Vazifang: Foydalanuvchi yuborgan mahsulot tarkibini (matn yoki rasm) tahlil qilish.

TAHLIL QOIDALARI:
1. 🔴 HAROM: Agar tarkibda cho'chqa yog'i, cho'chqa jelatini, karmin (E120), shellak (E904), L-sistein (odam yoki cho'chqa sochidan), spirt (alkogol, vino, konyak) bo'lsa.
2. 🟡 SHUBHALI (MASHBUH): Agar kelib chiqishi noma'lum jelatin, glitserin, mono- va diglitseridlar (E471), polisorbatlar bo'lsa va "o'simlikdan" deb aniq yozilmagan bo'lsa.
3. 🟢 HALOL: Agar tarkib toza bo'lsa (faqat o'simlik, sut, suv, tuz, sintetika va h.k.).
4. Agar yuborilgan narsa oziq-ovqat bo'lmasa -> "⚠️ Bu oziq-ovqat emas" deb ayt.

JAVOB FORMATI (O'zbek tilida):
---
🏷 **Mahsulot:** [Mahsulot nomini aniqla]
📊 **Status:** [🟢 HALOL / 🔴 HAROM / 🟡 SHUBHALI]

📝 **Tahlil:**
[Bu yerda qisqa va lo'nda tushuntir.]
---
"""

def analyze_text_with_ai(text_input):
    """Matnni AI orqali tekshirish"""
    try:
        response = model.generate_content(SYSTEM_PROMPT + f"\n\nTekshirilayotgan matn: {text_input}")
        return response.text
    except Exception as e:
        # Xatolikni chiroyli qilib chiqaramiz
        return f"⚠️ Uzr, serverda kichik muammo bo'ldi. Iltimos qaytadan urinib ko'ring.\n(Xato: {str(e)[:50]}...)"

def analyze_image_with_ai(image_path):
    """Rasmni AI Vision orqali tekshirish"""
    try:
        img = Image.open(image_path)
        response = model.generate_content([SYSTEM_PROMPT, img])
        return response.text
    except Exception as e:
        return f"⚠️ Rasmni o'qishda xatolik yuz berdi. Iltimos, tiniqroq rasm yuboring.\n(Xato: {str(e)[:50]}...)"
