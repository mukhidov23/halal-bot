import os
import base64
from groq import Groq

# --- 🔑 SIZNING GROQ KALITINGIZ ---
API_KEY = "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"

# Groq mijozini ulaymiz
client = Groq(api_key=API_KEY)

# Biz ishlatadigan model (Rasm va Matn uchun)
MODEL = "llama-3.2-11b-vision-preview"

# --- 🧠 TIZIM BUYRUQLARI ---
SYSTEM_PROMPT = """
Sen professional oziq-ovqat texnologi va Islomiy halol standarti ekspertisan.
Javobni faqat O'ZBEK tilida ber.

TAHLIL QOIDALARI:
1. 🔴 HAROM: Cho'chqa (yog', jelatin), Karmin (E120), Shellak (E904), L-sistein (odam/cho'chqa), Spirt/Alkogol, Vino, Konyak.
2. 🟡 SHUBHALI: Noma'lum jelatin, E471, glitserin, mono- va diglitseridlar (agar o'simlik deyilmasa).
3. 🟢 HALOL: Faqat o'simlik, sut, suv, tuz, sintetika, bo'yoqlar (E100-E199, karmin bundan mustasno).
4. Oziq-ovqat bo'lmasa -> "⚠️ Bu oziq-ovqat emas".

JAVOB FORMATI:
🏷 **Mahsulot:** [Nomini aniqla]
📊 **Status:** [🟢 HALOL / 🔴 HAROM / 🟡 SHUBHALI]

📝 **Tahlil:**
[Qisqa va aniq tushuntirish]
"""

# Rasmni kodga (base64) aylantirish funksiyasi
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_text_with_ai(text_input):
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Matnni tekshir: {text_input}"}
            ],
            temperature=0.1,
            max_tokens=600
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Groq xatosi: {e}"

def analyze_image_with_ai(image_path):
    try:
        # Rasmni tayyorlaymiz
        base64_image = encode_image(image_path)
        
        # Groqqa yuboramiz
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": SYSTEM_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            temperature=0.1,
            max_tokens=600
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Rasm tahlilida xatolik: {e}"
