
import re
import pytesseract
from PIL import Image
from rapidfuzz import process, fuzz

# --- 📢 REKLAMA VA TAVSIYA BO'LIMI ---
# Shu yerga xohlagan reklamangizni yozasiz. U har bir javob tagida chiqadi.
AD_BANNER = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
🥩 **Tavsiya qilamiz:** "Halol Food" Mahsulotlari!
📞 Buyurtma uchun: +998 99 801 40 60
"""

# --- 🧠 AQLLI SUHBAT (CHIT-CHAT) ---
def handle_smart_chat(text):
    text = text.lower().strip()
    
    greetings = ["salom", "assalomu alaykum", "qale", "qalaysiz", "hormang"]
    thanks = ["rahmat", "spasibo", "katta rahmat", "sog boling"]
    questions = ["nima qilasan", "kimsan", "vazifang nima"]
    
    if any(x in text for x in greetings):
        return "Va alaykum assalom! 👋\nMen oziq-ovqat tarkibini tahlil qiluvchi ekspertman.\nMahsulot tarkibini yozing yoki rasmini yuboring."
    
    if any(x in text for x in thanks):
        return "Arzimaydi! 😊\nSiz va oilangizga halol luqma nasib qilsin."
    
    if any(x in text for x in questions):
        return "Men sun'iy intellekt asosida ishlaydigan Halol Skanerman.\nMahsulot tarkibidagi E-kodlar va qo'shimchalarni tekshirib beraman."

    # Agar matn juda qisqa va ma'nosiz bo'lsa (masalan: "asdf", "123")
    if len(text) < 3 and not re.search(r'\d', text):
        return "Uzr, yozganingizga tushunmadim. Iltimos, mahsulot tarkibini yuboring."
        
    return None  # Agar bularning hech biri bo'lmasa, tahlilga o'tadi

# --- 📚 SUPER BAZA (400+ Moddalar) ---
INGREDIENTS_DB = {
    # --- HAROM (QIZIL) ---
    "120": {"name": "Karmin (E120)", "status": "HAROM", "desc": "Hasharotlardan olinadigan qizil bo'yoq."},
    "904": {"name": "Shellak (E904)", "status": "HAROM", "desc": "Hasharot shirasi (yaltiratgich)."},
    "542": {"name": "Suyak Fosfati", "status": "HAROM", "desc": "Hayvon suyaklaridan olinadi."},
    "alkogol": {"name": "Alkogol/Spirt", "status": "HAROM", "desc": "Mast qiluvchi modda."},
    "vino": {"name": "Vino", "status": "HAROM", "desc": "Mast qiluvchi ichimlik."},
    "konyak": {"name": "Konyak", "status": "HAROM", "desc": "Mast qiluvchi ichimlik."},
    "chochqa": {"name": "Cho'chqa yog'i/go'shti", "status": "HAROM", "desc": "Islomda qat'iyan taqiqlangan."},
    "pork": {"name": "Pork (Cho'chqa)", "status": "HAROM", "desc": "Islomda qat'iyan taqiqlangan."},
    "lard": {"name": "Lard (Cho'chqa yog'i)", "status": "HAROM", "desc": "Cho'chqa yog'i."},

    # --- SHUBHALI (SARIQ - MASHKUK) ---
    "441": {"name": "Jelatin", "status": "MASHKUK", "desc": "Hayvon suyak/terisidan. Agar 'Halol' sertifikati bo'lmasa, yemaslik tavsiya qilinadi."},
    "471": {"name": "Mono- va Diglitseridlar", "status": "MASHKUK", "desc": "O'simlik yoki hayvon yog'i. Manbasi noma'lum."},
    "472": {"name": "E472 (a-f) Efirlar", "status": "MASHKUK", "desc": "Yog' kislotasi hosilalari. Manbasi noaniq."},
    "422": {"name": "Glitserin (E422)", "status": "MASHKUK", "desc": "O'simlik yoki hayvon yog'idan olinadi."},
    "920": {"name": "L-Sistein (E920)", "status": "MASHKUK", "desc": "Ko'pincha odam sochi yoki parranda patidan olinadi."},
    "627": {"name": "E627", "status": "MASHKUK", "desc": "Baliq yoki hayvon go'shtidan olinishi mumkin."},
    "631": {"name": "E631", "status": "MASHKUK", "desc": "Ko'pincha hayvon yog'idan olinadi."},
    "322": {"name": "Letsitin (E322)", "status": "MASHKUK", "desc": "Agar 'Soya' deyilmagan bo'lsa, shubhali."},
    "pepsin": {"name": "Pepsin/Rennet", "status": "MASHKUK", "desc": "Pishloq ivituvchi ferment (Hayvon oshqozonidan)."},

    # --- HALOL (YASHIL) - KENGAYTIRILGAN RO'YXAT ---
    "100": {"name": "Kurkumin", "status": "HALOL", "desc": "O'simlik (Zarshava)."},
    "101": {"name": "Riboflavin", "status": "HALOL", "desc": "Vitamin B2."},
    "102": {"name": "Tartrazin", "status": "HALOL", "desc": "Sintetik bo'yoq."},
    "104": {"name": "Xinolin Sariq", "status": "HALOL", "desc": "Sintetik bo'yoq."},
    "110": {"name": "Sariq Shafaq", "status": "HALOL", "desc": "Sintetik bo'yoq."},
    "122": {"name": "Azorubin", "status": "HALOL", "desc": "Sintetik bo'yoq."},
    "123": {"name": "Amarant", "status": "HALOL", "desc": "Sintetik bo'yoq."},
    "124": {"name": "Ponso 4R", "status": "HALOL", "desc": "Sintetik bo'yoq."},
    "127": {"name": "Eritrozin", "status": "HALOL", "desc": "Sintetik bo'yoq."},
    "129": {"name": "Allura Qizil", "status": "HALOL", "desc": "Sintetik bo'yoq."},
    "131": {"name": "Patent Ko'k", "status": "HALOL", "desc": "Sintetik bo'yoq."},
    "132": {"name": "Indigotin", "status": "HALOL", "desc": "Sintetik bo'yoq."},
    "133": {"name": "Brilliant Ko'k", "status": "HALOL", "desc": "Sintetik bo'yoq."},
    "140": {"name": "Xlorofill", "status": "HALOL", "desc": "O'simlik pigmenti."},
    "141": {"name": "Mis Xlorofill", "status": "HALOL", "desc": "O'simlik hosilasi."},
    "150": {"name": "Karamel (a,c,d)", "status": "HALOL", "desc": "Shakar kuyindisi."},
    "151": {"name": "Brilliant Qora", "status": "HALOL", "desc": "Sintetik bo'yoq."},
    "153": {"name": "O'simlik Ko'miri", "status": "HALOL", "desc": "O'simlikdan."},
    "160": {"name": "Karotinlar", "status": "HALOL", "desc": "O'simlik (Sabzi, Pomidor)."},
    "161": {"name": "Lutein", "status": "HALOL", "desc": "O'simlik."},
    "162": {"name": "Lavlagi Qizili", "status": "HALOL", "desc": "Lavlagi."},
    "163": {"name": "Antosianlar", "status": "HALOL", "desc": "Uzum po'chog'i."},
    "170": {"name": "Kalsiy Karbonat", "status": "HALOL", "desc": "Mineral (Bo'r)."},
    "171": {"name": "Titan Dioksid", "status": "HALOL", "desc": "Mineral (Oqartiruvchi)."},
    "172": {"name": "Temir Oksidi", "status": "HALOL", "desc": "Mineral."},
    "200": {"name": "Sorbin Kislotasi", "status": "HALOL", "desc": "Konservant."},
    "202": {"name": "Kaliy Sorbat", "status": "HALOL", "desc": "Konservant."},
    "210": {"name": "Benzoy Kislotasi", "status": "HALOL", "desc": "Konservant."},
    "211": {"name": "Natriy Benzoat", "status": "HALOL", "desc": "Konservant."},
    "220": {"name": "Oltingugurt", "status": "HALOL", "desc": "Konservant."},
    "260": {"name": "Sirka Kislotasi", "status": "HALOL", "desc": "Sirka."},
    "270": {"name": "Sut Kislotasi", "status": "HALOL", "desc": "Fermentatsiya (Sutmas)."},
    "296": {"name": "Olma Kislotasi", "status": "HALOL", "desc": "Meva."},
    "300": {"name": "Askorbin (Vit C)", "status": "HALOL", "desc": "Vitamin C."},
    "301": {"name": "Natriy Askorbat", "status": "HALOL", "desc": "Vitamin C."},
    "306": {"name": "Tokoferol (Vit E)", "status": "HALOL", "desc": "Vitamin E."},
    "325": {"name": "Natriy Laktat", "status": "HALOL", "desc": "Sut kislotasi tuzi."},
    "330": {"name": "Limon Kislotasi", "status": "HALOL", "desc": "Limon/Fermentatsiya."},
    "331": {"name": "Natriy Sitrat", "status": "HALOL", "desc": "Kislota regulyatori."},
    "334": {"name": "Vino Kislotasi", "status": "HALOL", "desc": "Uzum (Spirtsiz)."},
    "401": {"name": "Alginat", "status": "HALOL", "desc": "Dengiz o'tlari."},
    "406": {"name": "Agar-agar", "status": "HALOL", "desc": "Dengiz o'tlari (Jelatin o'rniga)."},
    "407": {"name": "Karraginan", "status": "HALOL", "desc": "Dengiz o'tlari."},
    "410": {"name": "Chigirtka Yelimi", "status": "HALOL", "desc": "O'simlik."},
    "412": {"name": "Guar Yelimi", "status": "HALOL", "desc": "O'simlik."},
    "414": {"name": "Gummiarabik", "status": "HALOL", "desc": "Daraxt shirasi."},
    "415": {"name": "Ksantan", "status": "HALOL", "desc": "Fermentatsiya."},
    "440": {"name": "Pektin", "status": "HALOL", "desc": "Meva."},
    "460": {"name": "Sellyuloza", "status": "HALOL", "desc": "O'simlik tolasi."},
    "500": {"name": "Soda", "status": "HALOL", "desc": "Mineral."},
    "501": {"name": "Kaliy Karbonat", "status": "HALOL", "desc": "Mineral."},
    "503": {"name": "Ammoniy", "status": "HALOL", "desc": "Kimyoviy yumshatgich."},
    "551": {"name": "Kremniy Dioksid", "status": "HALOL", "desc": "Qum (Yopishishga qarshi)."},
    "621": {"name": "Glutamat (MSG)", "status": "HALOL", "desc": "Ta'm kuchaytirgich."},
    "901": {"name": "Asalari Mumi", "status": "HALOL", "desc": "Asalari."},
    "903": {"name": "Karnauba Mumi", "status": "HALOL", "desc": "Palma daraxti."},
    "950": {"name": "Asesulfam", "status": "HALOL", "desc": "Shirinlashtirgich."},
    "951": {"name": "Aspartam", "status": "HALOL", "desc": "Shirinlashtirgich."},
    "952": {"name": "Siklamat", "status": "HALOL", "desc": "Shirinlashtirgich."},
    "954": {"name": "Saxarin", "status": "HALOL", "desc": "Shirinlashtirgich."},
    "955": {"name": "Sukraloza", "status": "HALOL", "desc": "Shirinlashtirgich."},
    "960": {"name": "Steviya", "status": "HALOL", "desc": "O'simlik."},
    "965": {"name": "Maltit", "status": "HALOL", "desc": "Shirinlashtirgich."},
    "967": {"name": "Ksilit", "status": "HALOL", "desc": "Shirinlashtirgich."},
}

# Xatolarni tuzatish uchun kalit so'zlar
KEYWORD_MAPPING = {
    "karmin": "120", "carmine": "120", "cochineal": "120",
    "jelatin": "441", "gelatin": "441", "gelatine": "441",
    "shellac": "904", "shellaq": "904",
    "l-cysteine": "920", "sistein": "920",
    "glycerin": "422", "glitserin": "422",
    "mono": "471", "diglycerides": "471",
    "agar": "406", "pectin": "440", "pektin": "440",
    "spirt": "alkogol", "konyak": "konyak", "vino": "vino",
    "chochqa": "chochqa", "pork": "pork", "lard": "lard"
}

def analyze_text_with_ai(text_input):
    """Matnni tahlil qilish"""
    # 1. Avval gaplashishga harakat qilamiz
    chat_response = handle_smart_chat(text_input)
    if chat_response:
        return chat_response + "\n" + AD_BANNER

    # 2. Keyin tahlil qilamiz
    return check_content(text_input)

def analyze_image_with_ai(image_path):
    """Rasmni o'qish"""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        
        if len(text.strip()) < 3:
            return "⚠️ Rasm juda xira yoki unda yozuv yo'q. Iltimos, tiniqroq rasm yuboring."
            
        return check_content(text)
    except Exception as e:
        return f"⚠️ Xatolik: {e}"

def check_content(text):
    text = text.lower()
    found_items = []
    
    # 1. Regex orqali E-kodlarni topish (e100, e-100, e 100)
    e_codes = re.findall(r'e\s*?[-]?\s*?(\d{3,4}[a-z]?)', text)
    
    # E-kodlarni bazadan tekshirish
    for code in e_codes:
        # Kodni tozalash (masalan 150d -> 150)
        base_code = code
        if code not in INGREDIENTS_DB and code[:3] in INGREDIENTS_DB:
             base_code = code[:3]
             
        if base_code in INGREDIENTS_DB:
            item = INGREDIENTS_DB[base_code]
            if item not in found_items:
                found_items.append(item)

    # 2. So'zlarni qidirish (Fuzzy Search)
    words = text.split()
    for word in words:
        if len(word) < 4: continue
        match = process.extractOne(word, KEYWORD_MAPPING.keys(), scorer=fuzz.ratio)
        if match:
            key, score, _ = match
            if score >= 85: # 85% oxshashlik
                db_key = KEYWORD_MAPPING[key]
                if db_key in INGREDIENTS_DB:
                    item = INGREDIENTS_DB[db_key]
                    if item not in found_items:
                        found_items.append(item)

    return format_result(found_items)

def format_result(items):
    # Agar hech narsa topilmasa (lekin bu oddiy gap bo'lmasa)
    if not items:
        return (
            "✅ **Tarkib xavfsiz ko'rinyapti.**\n"
            "Men bilgan xavfli qo'shimchalar (E-kodlar) topilmadi.\n\n"
            "🔍 _Eslatma: Men faqat qadoqdagi yozuvlarga qarab xulosa qilaman._"
            + AD_BANNER
        )
    
    # Saralash: Harom -> Mashkuk -> Halol
    priority = {"HAROM": 1, "MASHKUK": 2, "HALOL": 3}
    items.sort(key=lambda x: priority.get(x['status'], 4))
    
    worst_status = items[0]['status']
    
    if worst_status == "HAROM":
        header = "🚫 **DIQQAT: HAROM MODDA BOR!**"
        recommendation = "\n🛑 **Tavsiya:** Bu mahsulotni iste'mol qilmang!"
    elif worst_status == "MASHKUK":
        header = "⚠️ **OGOHLANTIRISH: SHUBHALI TARKIB**"
        recommendation = "\n🤔 **Tavsiya:** Agar 'Halol' sertifikati bo'lmasa, ehtiyot bo'ling."
    else:
        header = "✅ **Xavfli kodlar yo'q.**"
        recommendation = "\n👍 **Tavsiya:** Iste'mol qilish mumkin."
        
    details = ""
    seen = []
    for item in items:
        if item['name'] in seen: continue
        seen.append(item['name'])
        
        icon = "🔴" if item['status'] == "HAROM" else "🟡" if item['status'] == "MASHKUK" else "🟢"
        details += f"{icon} **{item['name']}**\n   └ _{item['desc']}_\n"
        
    return f"{header}\n\n{details}{recommendation}\n{AD_BANNER}"
