import os
import base64
from openai import OpenAI

# --- 🔑 SIZNING OPENROUTER KALITINGIZ ---
API_KEY = "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"

# --- ⚙️ SOZLAMALAR ---
# Biz OpenRouter manzili orqali ulaymiz
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

# --- 🔥 MODEL TANLASH ---
# Hozirgi eng zo'r va TEKIN model (OpenRouterda):
# Google Gemini 2.0 Flash Lite (Juda tez va bepul)
MODEL = "google/gemini-2.0-flash-lite-preview-02-05:free"

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

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_text_with_ai(text_input):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Matnni tekshir: {text_input}"}
            ],
            extra_headers={
                "HTTP-Referer": "https://t.me/halal_bot", 
                "X-Title": "Halal Scanner Bot",
            }
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ OpenRouter xatosi: {e}"

def analyze_image_with_ai(image_path):
    try:
        base64_image = encode_image(image_path)
        
        response = client.chat.completions.create(
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
                            }
                        }
                    ]
                }
            ],
            extra_headers={
                "HTTP-Referer": "https://t.me/halal_bot", 
                "X-Title": "Halal Scanner Bot",
            }
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Rasm tahlilida xatolik: {e}"
