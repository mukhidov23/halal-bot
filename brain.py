import re
import pytesseract
from PIL import Image
from rapidfuzz import process, fuzz

# --- 📚 KATTA LUG'AT (DATABASE) ---
# Siz bergan ro'yxat va qo'shimchalar
INGREDIENTS_DB = {
    "100": {"name": "Curcumin", "status": "HALOL", "desc": "O'simlikdan olinadi (Zarshava)."},
    "101": {"name": "Riboflavin", "status": "HALOL", "desc": "Vitamin B2."},
    "120": {"name": "Carmine", "status": "HAROM", "desc": "🔴 Hasharot (Qizil qo'ng'iz)dan olinadi."},
    "122": {"name": "Azorubine", "status": "HALOL", "desc": "Sintetik qizil bo'yoq."},
    "124": {"name": "Ponceau 4R", "status": "HALOL", "desc": "Sintetik qizil bo'yoq."},
    "129": {"name": "Allura Red", "status": "HALOL", "desc": "Sintetik qizil bo'yoq."},
    "140": {"name": "Chlorophyll", "status": "HALOL", "desc": "O'simlik (Yashil rang)."},
    "141": {"name": "Copper Chlorophyllin", "status": "HALOL", "desc": "O'simlik hosilasi."},
    "150a": {"name": "Caramel I", "status": "HALOL", "desc": "Karamel (Shakar)."},
    "150d": {"name": "Caramel IV", "status": "MASHKUK", "desc": "🟡 Shakar, lekin ammiak usulida olingan."},
    "160a": {"name": "Beta-carotene", "status": "HALOL", "desc": "O'simlik (Sabzi rangi)."},
    "162": {"name": "Beetroot Red", "status": "HALOL", "desc": "Lavlagi qizili."},
    "200": {"name": "Sorbic Acid", "status": "HALOL", "desc": "Konservant."},
    "202": {"name": "Potassium Sorbate", "status": "HALOL", "desc": "Konservant."},
    "210": {"name": "Benzoic Acid", "status": "HALOL", "desc": "Konservant."},
    "211": {"name": "Sodium Benzoate", "status": "HALOL", "desc": "Konservant."},
    "220": {"name": "Sulfur Dioxide", "status": "HALOL", "desc": "Konservant."},
    "300": {"name": "Ascorbic Acid", "status": "HALOL", "desc": "Vitamin C."},
    "301": {"name": "Sodium Ascorbate", "status": "HALOL", "desc": "Vitamin C hosilasi."},
    "306": {"name": "Tocopherols", "status": "HALOL", "desc": "Vitamin E (O'simlik)."},
    "322": {"name": "Lecithin", "status": "MASHKUK", "desc": "🟡 Soya bo'lsa Halol. Tuxum/Hayvon bo'lsa shubhali."},
    "330": {"name": "Citric Acid", "status": "HALOL", "desc": "Limon kislotasi."},
    "331": {"name": "Sodium Citrate", "status": "HALOL", "desc": "Kislota regulyatori."},
    "407": {"name": "Carrageenan", "status": "HALOL", "desc": "Dengiz o'tlari."},
    "410": {"name": "Locust Bean Gum", "status": "HALOL", "desc": "Daraxt urug'i."},
    "412": {"name": "Guar Gum", "status": "HALOL", "desc": "O'simlik yelimi."},
    "415": {"name": "Xanthan Gum", "status": "HALOL", "desc": "Fermentatsiya mahsuloti."},
    "420": {"name": "Sorbitol", "status": "HALOL", "desc": "Shirinlashtirgich."},
    "421": {"name": "Mannitol", "status": "HALOL", "desc": "Shirinlashtirgich."},
    "441": {"name": "Gelatin", "status": "MASHKUK", "desc": "🟡 Hayvon terisi/suyagi. Mol (Halol) yoki Cho'chqa (Harom)."},
    "471": {"name": "Mono- and Diglycerides", "status": "MASHKUK", "desc": "🟡 Yog' kislotalari. O'simlik yoki Hayvon yog'i bo'lishi mumkin."},
    "472": {"name": "Esters of Mono- Diglycerides", "status": "MASHKUK", "desc": "🟡 Yog' kislotasi efirlari."},
    "500": {"name": "Sodium Carbonate", "status": "HALOL", "desc": "Soda."},
    "503": {"name": "Ammonium Carbonate", "status": "HALOL", "desc": "Yumshatgich."},
    "621": {"name": "MSG (Glutamat)", "status": "HALOL", "desc": "Ta'm kuchaytirgich."},
    "627": {"name": "Disodium Guanylate", "status": "MASHKUK", "desc": "🟡 Baliq yoki Hayvon go'shti."},
    "631": {"name": "Disodium Inosinate", "status": "MASHKUK", "desc": "🟡 Ko'pincha cho'chqa yog'idan olinadi."},
    "904": {"name": "Shellac", "status": "HAROM", "desc": "🔴 Hasharot shirasi (Yaltiratgich)."},
    "920": {"name": "L-Cysteine", "status": "MASHKUK", "desc": "🟡 Odam sochi yoki hayvon juni."},
    "1200": {"name": "Polydextrose", "status": "HALOL", "desc": "Tola."},
}

# Kalit so'zlar (Imlo xatolarini tuzatish uchun)
KEYWORD_MAPPING = {
    "karmin": "120", "carmine": "120", "karmine": "120",
    "jelatin": "441", "gelatin": "441", "gelatine": "441",
    "shellac": "904", "shellaq": "904", "shilak": "904",
    "chochqa": "HAROM_TEXT", "pork": "HAROM_TEXT", "svina": "HAROM_TEXT",
    "konyak": "HAROM_TEXT", "spirt": "HAROM_TEXT", "alkogol": "HAROM_TEXT", "wine": "HAROM_TEXT"
}

def analyze_text_with_ai(text_input):
    """Matnni tahlil qilish (Lokal)"""
    return check_content(text_input)

def analyze_image_with_ai(image_path):
    """Rasmni o'qish va tahlil qilish (Tesseract)"""
    try:
        img = Image.open(image_path)
        # Rasmni o'qish
        text = pytesseract.image_to_string(img)
        
        if len(text.strip()) < 3:
            return "⚠️ Rasmda yozuv topilmadi yoki juda xira."
            
        return check_content(text)
    except Exception as e:
        return f"⚠️ Xatolik: {e}"

def check_content(text):
    text = text.lower()
    found_items = []
    
    # 1. E-KODLARNI QIDIRISH (Regex - "Cımbız" usuli)
    # Bu kod: e120, e-120, e 120, e120e140 (yopishgan) hammasini topadi
    e_codes = re.findall(r'[ehe]\s*?[-]?\s*?(\d{3,4}[a-z]?)', text)
    
    for code in e_codes:
        if code in INGREDIENTS_DB:
            found_items.append(INGREDIENTS_DB[code])

    # 2. SO'ZLARNI QIDIRISH (Fuzzy Search - Xatolarni tuzatish)
    words = text.split()
    for word in words:
        # Har bir so'zni bazadagi nomlar bilan solishtiramiz
        match = process.extractOne(word, KEYWORD_MAPPING.keys(), scorer=fuzz.ratio)
        if match:
            key, score, _ = match
            if score >= 85: # 85% oxshashlik bo'lsa
                val = KEYWORD_MAPPING[key]
                if val == "HAROM_TEXT":
                    found_items.append({"name": key.upper(), "status": "HAROM", "desc": "Tarkibda taqiqlangan so'z topildi."})
                elif val in INGREDIENTS_DB:
                    # Agar avval topilmagan bo'lsa qosh
                    if INGREDIENTS_DB[val] not in found_items:
                        found_items.append(INGREDIENTS_DB[val])

    return format_result(found_items)

def format_result(items):
    if not items:
        return "✅ **Xavfli kodlar topilmadi.**\n(Lekin ehtiyot bo'ling, men faqat bazadagi kodlarni bilaman)."
    
    # Saralash: Harom -> Mashkuk -> Halol
    priority = {"HAROM": 1, "MASHKUK": 2, "HALOL": 3}
    items.sort(key=lambda x: priority.get(x['status'], 4))
    
    # Eng yomon statusni aniqlash
    worst_status = items[0]['status']
    
    if worst_status == "HAROM":
        header = "🚫 **DIQQAT: HAROM MODDA TOPILDI!**"
    elif worst_status == "MASHKUK":
        header = "⚠️ **OGOHLANTIRISH: SHUBHALI TARKIB**"
    else:
        header = "✅ **Barchasi Halol (Bazaga ko'ra)**"
        
    result = f"{header}\n\n"
    seen = []
    
    for item in items:
        if item['name'] in seen: continue
        seen.append(item['name'])
        
        icon = "🔴" if item['status'] == "HAROM" else "🟡" if item['status'] == "MASHKUK" else "🟢"
        result += f"{icon} **{item['name']}** ({item['status']})\n   └ _{item['desc']}_\n\n"
        
    return result
