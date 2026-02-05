import google.generativeai as genai
import os
from PIL import Image

# --- 🔑 SIZNING KALITINGIZ ---
API_KEY = "AIzaSyC5QZ-GMyg30wmCEmlHO0g2NW4JZiQD2ms"

# Googleni sozlaymiz
genai.configure(api_key=API_KEY)

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

# Biz sinab ko'radigan modellar ro'yxati (Ketma-ket tekshiradi)
MODELS_TO_TRY = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-pro",
    "gemini-1.5-pro-001",
    "gemini-pro-vision"  # Eski ishonchli versiya (zaxira)
]

def ask_ai_universal(content_list):
    """Barcha modellarni birma-bir sinab ko'ruvchi funksiya"""
    errors = []
    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(content_list)
            return response.text
        except Exception as e:
            errors.append(f"{model_name}: {str(e)[:20]}")
            continue # Keyingi modelga o'tish
    
    # Agar hammasi o'xshamasa:
    return f"⚠️ Serverda texnik nosozlik. Hamma modellar band.\nXatolar: {', '.join(errors)}"

def analyze_text_with_ai(text_input):
    return ask_ai_universal([SYSTEM_PROMPT + f"\n\nMatn: {text_input}"])

def analyze_image_with_ai(image_path):
    try:
        img = Image.open(image_path)
        return ask_ai_universal([SYSTEM_PROMPT, img])
    except Exception as e:
        return f"⚠️ Rasmni ochishda xatolik: {e}"
