import google.generativeai as genai
import os
from PIL import Image

# --- 🔑 YANGI KALIT ---
API_KEY = "AIzaSyC5IRLgBtXRYZBbo9lE5lMMqNh1PIG98i8"

# Googleni sozlaymiz
genai.configure(api_key=API_KEY)

# --- 🧠 MODELNI AVTOMATIK TOPISH ---
def get_best_model():
    try:
        # Google-dan bor modellarni ro'yxatini so'raymiz
        for m in genai.list_models():
            # Agar model matn va rasm yarata olsa (generateContent), shuni olamiz
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: # Flash modelni afzal ko'ramiz (tezligi uchun)
                    return genai.GenerativeModel(m.name)
        
        # Agar Flash topilmasa, birinchi uchragan ishlaydigan modelni olamiz
        for m in genai.list_models():
             if 'generateContent' in m.supported_generation_methods:
                 return genai.GenerativeModel(m.name)
                 
    except Exception as e:
        print(f"Model qidirishda xato: {e}")
    
    # Hech narsa topilmasa, majburan standartini qo'yamiz
    return genai.GenerativeModel('gemini-1.5-flash')

# Modelni ishga tushiramiz
model = get_best_model()

# --- 🧠 SYSTEM PROMPT ---
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
    try:
        response = model.generate_content(SYSTEM_PROMPT + f"\n\nMatn: {text_input}")
        return response.text
    except Exception as e:
        return f"⚠️ Xatolik: {e}\n(Model: {model.model_name if hasattr(model, 'model_name') else 'Noma\'lum'})"

def analyze_image_with_ai(image_path):
    try:
        img = Image.open(image_path)
        response = model.generate_content([SYSTEM_PROMPT, img])
        return response.text
    except Exception as e:
        return f"⚠️ Rasmni ochishda xatolik: {e}"
