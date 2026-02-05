import requests
import base64
import os

# --- 🔑 YANGI KALIT ---
API_KEY = "AIzaSyC5IRLgBtXRYZBbo9lE5lMMqNh1PIG98i8"

# --- ⚙️ SOZLAMALAR ---
# Biz SDK ishlatmaymiz, to'g'ridan-to'g'ri URL ga yozamiz
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# --- 🧠 SYSTEM PROMPT ---
SYSTEM_PROMPT = """
Sen professional oziq-ovqat texnologi va Islomiy halol standarti ekspertisan.
Javobni O'ZBEK tilida ber.

TAHLIL QOIDALARI:
1. 🔴 HAROM: Cho'chqa (yog', jelatin), Karmin (E120), Shellak (E904), L-sistein (odam/cho'chqa), Alkogol.
2. 🟡 SHUBHALI: Noma'lum jelatin, E471, glitserin (agar o'simlik deyilmasa).
3. 🟢 HALOL: Faqat o'simlik, sut, suv, tuz, sintetika.
4. Oziq-ovqat bo'lmasa -> "⚠️ Bu oziq-ovqat emas".

JAVOB FORMATI:
🏷 Mahsulot: [Nom]
📊 Status: [🟢 HALOL / 🔴 HAROM / 🟡 SHUBHALI]
📝 Tahlil: [Qisqa tushuntirish]
"""

def send_request(payload):
    """Googlega to'g'ridan-to'g'ri xat yuborish"""
    try:
        response = requests.post(URL, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            result = response.json()
            # Javobni ichidan kerakli matnni kovlab olamiz
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except:
                return "⚠️ Tushunarsiz javob keldi."
        else:
            return f"⚠️ Xatolik (Kod {response.status_code}): {response.text[:100]}"
            
    except Exception as e:
        return f"⚠️ Internet xatosi: {e}"

def analyze_text_with_ai(text_input):
    payload = {
        "contents": [{
            "parts": [
                {"text": SYSTEM_PROMPT},
                {"text": f"Tekshirilayotgan matn: {text_input}"}
            ]
        }]
    }
    return send_request(payload)

def analyze_image_with_ai(image_path):
    try:
        # Rasmni kodga aylantiramiz (Base64)
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        payload = {
            "contents": [{
                "parts": [
                    {"text": SYSTEM_PROMPT},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_data
                        }
                    }
                ]
            }]
        }
        return send_request(payload)
    except Exception as e:
        return f"⚠️ Rasmni tayyorlashda xato: {e}"
