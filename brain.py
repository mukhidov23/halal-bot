import google.generativeai as genai
import os
from PIL import Image

# --- 🔑 YANGI KALIT ---
API_KEY = "AIzaSyC5IRLgBtXRYZBbo9lE5lMMqNh1PIG98i8"

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

# --- 🔥 ENG MUHIM JOYI: UNIVERSAL FUNKSIYA ---
def generate_content_safe(contents):
    # Biz sinab ko'radigan modellar ro'yxati (Ketma-ketlikda)
    models_to_try = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro",         # Eski matn modeli
        "gemini-pro-vision"   # Eski rasm modeli
    ]
    
    last_error = ""
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(contents)
            return response.text
        except Exception as e:
            # Agar xato bersa, keyingi modelga o'tamiz
            last_error = str(e)
            continue

    # Agar hammasi o'xshamasa:
    return f"⚠️ Uzr, serverda hamma modellar band.\nXato: {last_error[:100]}"

def analyze_text_with_ai(text_input):
    return generate_content_safe(SYSTEM_PROMPT + f"\n\nMatn: {text_input}")

def analyze_image_with_ai(image_path):
    try:
        img = Image.open(image_path)
        # Prompt va Rasmni birga yuboramiz
        return generate_content_safe([SYSTEM_PROMPT, img])
    except Exception as e:
        return f"⚠️ Rasmni ochishda xatolik: {e}"
