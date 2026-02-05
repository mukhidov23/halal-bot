import google.generativeai as genai
import os
from PIL import Image

# --- 🔑 SIZNING KALITINGIZ ---
# Diqqat: Bu kalitni boshqa joyda ko'rsatmang!
API_KEY = "AIzaSyC5QZ-GMyg30wmCEmlHO0g2NW4JZiQD2ms"

# Googleni sozlaymiz
genai.configure(api_key=API_KEY)

# Modelni tanlaymiz (Gemini 1.5 Flash - eng tez va tekin versiya)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 🧠 BOTNING MIYASI (Ekspert Prompt) ---
# Bu yerda biz AI ga o'zini kim deb his qilishini o'rgatamiz
SYSTEM_PROMPT = """
Sen professional oziq-ovqat texnologi va Islomiy halol standarti ekspertisan.
Sening vazifang: Foydalanuvchi yuborgan mahsulot tarkibini (matn yoki rasm) chuqur tahlil qilish.

TAHLIL QOIDALARI:
1. 🔴 HAROM: Agar tarkibda cho'chqa yog'i, cho'chqa jelatini, karmin (E120), shellak (E904), L-sistein (odam yoki cho'chqa sochidan), spirt (alkogol, vino, konyak) bo'lsa.
2. 🟡 SHUBHALI (MASHBUH): Agar kelib chiqishi noma'lum jelatin, glitserin, mono- va diglitseridlar (E471), polisorbatlar bo'lsa va "o'simlikdan" deb aniq yozilmagan bo'lsa.
3. 🟢 HALOL: Agar tarkib toza bo'lsa (faqat o'simlik, sut, suv, tuz, sintetika va h.k.).
4. Agar yuborilgan narsa oziq-ovqat bo'lmasa -> "⚠️ Bu oziq-ovqat emas" deb ayt.

JAVOB FORMATI (O'zbek tilida):
---
🏷 **Mahsulot:** [Mahsulot nomini aniqla, masalan: "Lays Chipsi (Piyozli)"]
📊 **Status:** [🟢 HALOL / 🔴 HAROM / 🟡 SHUBHALI]

📝 **Tahlil:**
[Bu yerda qisqa va lo'nda tushuntir. Masalan: "Tarkibida E120 (Karmin) bo'yog'i bor, bu hasharotdan olinadi va harom hisoblanadi."]
---
"""

def analyze_text_with_ai(text_input):
    """Matnni AI orqali tekshirish"""
    try:
        response = model.generate_content(SYSTEM_PROMPT + f"\n\nTekshirilayotgan matn: {text_input}")
        return response.text
    except Exception as e:
        return f"⚠️ Tizimda xatolik: {e}"

def analyze_image_with_ai(image_path):
    """Rasmni AI Vision orqali tekshirish"""
    try:
        img = Image.open(image_path)
        # AIga ham promptni, ham rasmni beramiz
        response = model.generate_content([SYSTEM_PROMPT, img])
        return response.text
    except Exception as e:
        return f"⚠️ Rasmni o'qishda xatolik: {e}"import asyncio
import os
import re
from dataclasses import dataclass
from typing import List
from rapidfuzz import process, fuzz

try:
    from PIL import Image
    import pytesseract
except ImportError:
    print("Diqqat: Pillow yoki pytesseract o'rnatilmagan!")

# --- 1. DATA MODELLAR ---
@dataclass
class Ingredient:
    code: str
    names: List[str]
    status: str
    description: str
    risk_level: int

# --- 2. SUPER MA'LUMOTLAR BAZASI ---
INGREDIENTS_DB = [
    # =========================================================================
    # 🔴 HAROM (ENG XAVFLILARI - Qizil)
    # =========================================================================
    Ingredient("E120", ["e120", "carmine", "karmin", "кармин", "cochineal", "carminic acid"], "HAROM", "Manba: Hasharot (Qizil rang).", 10),
    Ingredient("E904", ["e904", "shellac", "shellaq", "шеллак"], "HAROM", "Manba: Hasharot (Yaltiratgich).", 10),
    Ingredient("E542", ["e542", "bone phosphate", "fosfat", "костный фосфат"], "HAROM", "Manba: Hayvon suyaklari.", 10),
    Ingredient("ALCOHOL", ["spirt", "etanol", "alcohol", "wine", "konyak", "спирт", "алкоголь", "ethanol"], "HAROM", "Manba: Mast qiluvchi modda.", 10),
    Ingredient("E441", ["e441", "gelatin", "jelatin", "gelatine", "желатин"], "SHUBHALI", "Agar 'Mol go'shti' yoki 'Halol' deb yozilmagan bo'lsa - HAROM.", 9),
    Ingredient("E920", ["e920", "l-cysteine", "l-sistein", "цистеин"], "SHUBHALI", "Manba: Inson sochi yoki cho'chqa yungi bo'lishi mumkin.", 9),
    Ingredient("E921", ["e921", "l-cystine", "sistin", "цистин"], "SHUBHALI", "Manba: Hayvon yungi yoki soch.", 9),

    # =========================================================================
    # 🟡 SHUBHALI (Hayvon yog'i bo'lishi ehtimoli bor - Sariq)
    # =========================================================================
    # Emulgatorlar (Eng ko'p uchraydigan shubhali guruh)
    Ingredient("E470a", ["e470a", "sodium salts of fatty acids", "yog' kislotalari tuzlari"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i.", 7),
    Ingredient("E470b", ["e470b", "magnesium salts", "magniy tuzlari"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i.", 7),
    Ingredient("E471", ["e471", "mono- and diglycerides", "yog' kislotalari", "диглицериды"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i (Aniqlashtirish kerak).", 7),
    Ingredient("E472a", ["e472a", "acetic acid esters", "sirka kislotasi efirlari"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i.", 7),
    Ingredient("E472b", ["e472b", "lactic acid esters", "sut kislotasi efirlari"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i.", 7),
    Ingredient("E472c", ["e472c", "citric acid esters", "limon kislotasi efirlari"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i.", 7),
    Ingredient("E472e", ["e472e", "datem", "tartaric acid esters", "эфиры"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i.", 7),
    Ingredient("E473", ["e473", "sucrose esters", "saxaroza efirlari"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i.", 7),
    Ingredient("E474", ["e474", "sucroglycerides", "saxarogliseridlar"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i.", 7),
    Ingredient("E475", ["e475", "polyglycerol esters", "poligliserin"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i.", 7),
    Ingredient("E476", ["e476", "polyglycerol polyricinoleate", "pgpr", "полиглицерин"], "SHUBHALI", "Manba: O'simlik (Halol) yoki Hayvon (Shubhali).", 6),
    Ingredient("E477", ["e477", "propane-1,2-diol esters", "propilen glikol"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i.", 7),
    Ingredient("E479b", ["e479b", "thermally oxidized soya bean oil"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i.", 6),
    Ingredient("E481", ["e481", "sodium stearoyl-2-lactylate", "stearoil"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i.", 7),
    Ingredient("E482", ["e482", "calcium stearoyl-2-lactylate", "kalsiy stearoil"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i.", 7),
    
    # Boshqa shubhalilar
    Ingredient("E150d", ["e150d", "caramel iv", "karamel", "сахарный колер"], "SHUBHALI", "Manba: Shakar (Ishlov berishda shubha bor).", 6),
    Ingredient("E322", ["e322", "lecithin", "lebitsin", "лецитин"], "SHUBHALI", "Manba: Soya (Halol) yoki Hayvon/Tuxum (Shubhali).", 5),
    Ingredient("E422", ["e422", "glycerol", "glycerin", "глицерин"], "SHUBHALI", "Manba: O'simlik yoki Hayvon yog'i.", 6),
    Ingredient("E627", ["e627", "disodium guanylate", "гуанилат"], "SHUBHALI", "Manba: Baliq yoki Hayvon (Cho'chqa bo'lishi mumkin).", 6),
    Ingredient("E631", ["e631", "disodium inosinate", "инозинат"], "SHUBHALI", "Manba: Go'sht yoki Baliq.", 6),
    Ingredient("E635", ["e635", "disodium 5-ribonucleotides", "ribonukleotidlar"], "SHUBHALI", "Manba: Hayvon (Cho'chqa).", 7),
    Ingredient("E1105", ["e1105", "lysozyme", "lizotsim"], "SHUBHALI", "Manba: Tuxum oqsili (Tovuq manbasi muhim).", 5),

    # =========================================================================
    # 🟢 HALOL (O'SIMLIK, MINERAL YOKI SINTETIK - Yashil)
    # =========================================================================
    
    # BO'YOQLAR (Colors)
    Ingredient("E100", ["e100", "curcumin", "kurkumin", "куркумин"], "HALOL", "Manba: O'simlik (Sariq).", 0),
    Ingredient("E101", ["e101", "riboflavin", "vitamin b2", "рибофлавин"], "HALOL", "Manba: Sintetik/O'simlik.", 0),
    Ingredient("E102", ["e102", "tartrazine", "tartrazin", "тартразин"], "HALOL", "Manba: Sintetik (Zararli bo'lishi mumkin).", 2),
    Ingredient("E104", ["e104", "quinoline yellow", "xinolin"], "HALOL", "Manba: Sintetik.", 2),
    Ingredient("E110", ["e110", "sunset yellow", "sariq shafaq"], "HALOL", "Manba: Sintetik.", 2),
    Ingredient("E122", ["e122", "azorubine", "karmoizin", "азорубин"], "HALOL", "Manba: Sintetik.", 2),
    Ingredient("E123", ["e123", "amaranth", "amarant"], "HALOL", "Manba: Sintetik (Lekin ko'p davlatda taqiqlangan).", 3),
    Ingredient("E124", ["e124", "ponceau 4r", "ponso"], "HALOL", "Manba: Sintetik.", 2),
    Ingredient("E127", ["e127", "erythrosine", "eritrozin"], "HALOL", "Manba: Sintetik.", 2),
    Ingredient("E129", ["e129", "allura red", "allyura"], "HALOL", "Manba: Sintetik.", 2),
    Ingredient("E131", ["e131", "patent blue", "ko'k patent"], "HALOL", "Manba: Sintetik.", 2),
    Ingredient("E132", ["e132", "indigotine", "indigo"], "HALOL", "Manba: Sintetik.", 2),
    Ingredient("E133", ["e133", "brilliant blue", "ko'k brilliant", "синий блестящий"], "HALOL", "Manba: Sintetik.", 1),
    Ingredient("E140", ["e140", "chlorophyll", "xlorofill", "хлорофилл"], "HALOL", "Manba: O'simlik.", 0),
    Ingredient("E141", ["e141", "copper chlorophyllin", "mis xlorofill"], "HALOL", "Manba: O'simlik.", 0),
    Ingredient("E150a", ["e150a", "plain caramel", "karamel i"], "HALOL", "Manba: Shakar.", 0),
    Ingredient("E150c", ["e150c", "ammonia caramel", "karamel iii"], "HALOL", "Manba: Shakar.", 0),
    Ingredient("E151", ["e151", "brilliant black", "qora brilliant"], "HALOL", "Manba: Sintetik.", 2),
    Ingredient("E153", ["e153", "vegetable carbon", "ko'mir"], "HALOL", "Manba: O'simlik ko'miri.", 0),
    Ingredient("E155", ["e155", "brown ht", "jigarrang"], "HALOL", "Manba: Sintetik.", 2),
    Ingredient("E160a", ["e160a", "beta-carotene", "karotin", "каротин"], "HALOL", "Manba: O'simlik.", 0),
    Ingredient("E160c", ["e160c", "paprika extract", "paprika"], "HALOL", "Manba: Qalampir.", 0),
    Ingredient("E162", ["e162", "beetroot red", "lavlagi", "свекольный красный"], "HALOL", "Manba: Lavlagi.", 0),
    Ingredient("E163", ["e163", "anthocyanins", "antosianlar"], "HALOL", "Manba: Uzum/Meva.", 0),
    Ingredient("E170", ["e170", "calcium carbonate", "bo'r", "карбонат кальция"], "HALOL", "Manba: Mineral.", 0),
    Ingredient("E171", ["e171", "titanium dioxide", "titan dioksidi"], "HALOL", "Manba: Mineral (Oqartiruvchi).", 3),
    Ingredient("E172", ["e172", "iron oxides", "temir oksidi"], "HALOL", "Manba: Mineral.", 0),

    # KONSERVANTLAR
    Ingredient("E200", ["e200", "sorbic acid", "sorbin kislotasi"], "HALOL", "Manba: Sintetik.", 0),
    Ingredient("E202", ["e202", "potassium sorbate", "sorbat kaliy", "сорбат калия"], "HALOL", "Manba: Sintetik.", 0),
    Ingredient("E210", ["e210", "benzoic acid", "benzoy kislotasi"], "HALOL", "Manba: Sintetik.", 0),
    Ingredient("E211", ["e211", "sodium benzoate", "benzoat natriy", "бензоат натрия"], "HALOL", "Manba: Sintetik.", 1),
    Ingredient("E220", ["e220", "sulfur dioxide", "oltingugurt"], "HALOL", "Manba: Sintetik.", 1),
    Ingredient("E250", ["e250", "sodium nitrite", "nitrit natriy"], "HALOL", "Manba: Sintetik (Zararli).", 3),
    Ingredient("E251", ["e251", "sodium nitrate", "nitrat natriy"], "HALOL", "Manba: Sintetik.", 3),
    Ingredient("E260", ["e260", "acetic acid", "sirka kislotasi"], "HALOL", "Manba: Sirka.", 0),
    Ingredient("E270", ["e270", "lactic acid", "sut kislotasi"], "HALOL", "Manba: Fermentatsiya.", 0),
    Ingredient("E296", ["e296", "malic acid", "olma kislotasi"], "HALOL", "Manba: Sintetik.", 0),

    # ANTIOKSIDANTLAR
    Ingredient("E300", ["e300", "ascorbic acid", "vitamin c"], "HALOL", "Manba: Vitamin C.", 0),
    Ingredient("E301", ["e301", "sodium ascorbate", "askorbat natriy"], "HALOL", "Manba: Sintetik.", 0),
    Ingredient("E306", ["e306", "tocopherols", "vitamin e"], "HALOL", "Manba: O'simlik.", 0),
    Ingredient("E307", ["e307", "alpha-tocopherol", "alfa-tokoferol"], "HALOL", "Manba: Sintetik.", 0),
    Ingredient("E320", ["e320", "bha", "butilgidroksianizol"], "HALOL", "Manba: Sintetik (Zararli).", 4),
    Ingredient("E321", ["e321", "bht", "butilgidroksitoluen"], "HALOL", "Manba: Sintetik (Zararli).", 4),
    Ingredient("E330", ["e330", "citric acid", "limon kislotasi", "лимонная кислота"], "HALOL", "Manba: Limon/Fermentatsiya.", 0),
    Ingredient("E331", ["e331", "sodium citrate", "sitrat natriy"], "HALOL", "Manba: Sintetik.", 0),
    Ingredient("E338", ["e338", "phosphoric acid", "fosfor kislotasi"], "HALOL", "Manba: Mineral.", 0),
    Ingredient("E339", ["e339", "sodium phosphates", "fosfat natriy"], "HALOL", "Manba: Mineral.", 0),
    Ingredient("E340", ["e340", "potassium phosphates", "fosfat kaliy"], "HALOL", "Manba: Mineral.", 0),
    Ingredient("E341", ["e341", "calcium phosphates", "kalsiy fosfat"], "HALOL", "Manba: Mineral.", 0),

    # QUYULTIRGICHLAR (Thickeners)
    Ingredient("E401", ["e401", "sodium alginate", "alginat natriy"], "HALOL", "Manba: Dengiz o'tlari.", 0),
    Ingredient("E406", ["e406", "agar", "agar-agar"], "HALOL", "Manba: Dengiz o'tlari.", 0),
    Ingredient("E407", ["e407", "carrageenan", "karraginan", "каррагинан"], "HALOL", "Manba: Dengiz o'tlari.", 0),
    Ingredient("E410", ["e410", "locust bean gum", "chigirtka yelimi"], "HALOL", "Manba: O'simlik.", 0),
    Ingredient("E412", ["e412", "guar gum", "guar", "гуаровая камедь"], "HALOL", "Manba: O'simlik urug'i.", 0),
    Ingredient("E414", ["e414", "gum arabic", "gummiarabik"], "HALOL", "Manba: Daraxt shirasi.", 0),
    Ingredient("E415", ["e415", "xanthan gum", "ksantan", "ксантановая камедь"], "HALOL", "Manba: Fermentatsiya.", 0),
    Ingredient("E440", ["e440", "pectin", "pektin", "пектин"], "HALOL", "Manba: Meva po'chog'i.", 0),
    Ingredient("E450", ["e450", "diphosphates", "difosfat"], "HALOL", "Manba: Mineral.", 0),
    Ingredient("E451", ["e451", "triphosphates", "trifosfat"], "HALOL", "Manba: Mineral.", 0),
    Ingredient("E452", ["e452", "polyphosphates", "polifosfat"], "HALOL", "Manba: Mineral.", 0),
    Ingredient("E460", ["e460", "cellulose", "sellyuloza", "целлюлоза"], "HALOL", "Manba: O'simlik.", 0),
    Ingredient("E466", ["e466", "cmc", "karboksimetilsellyuloza"], "HALOL", "Manba: Sintetik/O'simlik.", 0),

    # KRAXMALLAR VA BOSHQALAR
    Ingredient("E1404", ["e1404", "oxidized starch", "kraxmal"], "HALOL", "Manba: O'simlik.", 0),
    Ingredient("E1412", ["e1412", "distarch phosphate", "fosfat kraxmal"], "HALOL", "Manba: O'simlik.", 0),
    Ingredient("E1422", ["e1422", "acetylated distarch adipate", "kraxmal"], "HALOL", "Manba: O'simlik.", 0),
    Ingredient("E1442", ["e1442", "modified starch", "modifikatsiyalangan kraxmal"], "HALOL", "Manba: O'simlik.", 0),
    Ingredient("E500", ["e500", "sodium carbonate", "soda", "сода"], "HALOL", "Manba: Mineral.", 0),
    Ingredient("E503", ["e503", "ammonium carbonate", "ammoniy"], "HALOL", "Manba: Sintetik.", 0),
    Ingredient("E621", ["e621", "msg", "glutamat", "глутамат"], "HALOL", "Manba: Fermentatsiya (Zararli bo'lishi mumkin).", 2),
    Ingredient("E901", ["e901", "beeswax", "asalari mumi"], "HALOL", "Manba: Asalari.", 0),
    Ingredient("E903", ["e903", "carnauba wax", "karnauba mumi"], "HALOL", "Manba: Palma daraxti.", 0),
    Ingredient("E950", ["e950", "acesulfame k", "asesulfam"], "HALOL", "Manba: Sintetik (Shirinlashtirgich).", 0),
    Ingredient("E951", ["e951", "aspartame", "aspartam"], "HALOL", "Manba: Sintetik.", 0),
    Ingredient("E952", ["e952", "cyclamic acid", "siklamat"], "HALOL", "Manba: Sintetik.", 0),
    Ingredient("E954", ["e954", "saccharin", "saxarin"], "HALOL", "Manba: Sintetik.", 0),
    Ingredient("E955", ["e955", "sucralose", "sukraloza"], "HALOL", "Manba: Sintetik.", 0),
    Ingredient("E965", ["e965", "maltitol", "maltit"], "HALOL", "Manba: O'simlik.", 0),
    Ingredient("E967", ["e967", "xylitol", "ksilit"], "HALOL", "Manba: O'simlik.", 0),
    Ingredient("PALM", ["palm oil", "palma yog'i", "пальмовое масло"], "ZARARLI", "Manba: O'simlik (Tomir to'sadi).", 4),
]

# --- 3. LOGIKA ---
class HalolScannerEngine:
    def __init__(self, db: List[Ingredient]):
        self.db = db
        self.all_keywords = {}
        for ing in self.db:
            for name in ing.names:
                self.all_keywords[name] = ing

    def scan_image(self, image_path: str) -> dict:
        try:
            img = Image.open(image_path)
            # Rus va Ingliz tili baravar o'qiladi
            text = pytesseract.image_to_string(img) 
            
            if len(text.strip()) < 3:
                return {"status": "ERROR", "message": "Yozuvni o'qiyolmadim."}
            
            return self.check_text(text)
        except Exception as e:
            return {"status": "ERROR", "message": f"Xatolik: {e}"}

    def check_text(self, text: str) -> dict:
        found_issues = []
        # Tozalash
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = clean_text.split()
        
        for word in words:
            if len(word) < 2: continue
            
            # Fuzzy Search (90% aniqlik)
            match = process.extractOne(word, self.all_keywords.keys(), scorer=fuzz.ratio)
            if match:
                matched_word, score, _ = match
                if score >= 90:
                    ingredient = self.all_keywords[matched_word]
                    if ingredient not in [x['ingredient'] for x in found_issues]:
                        found_issues.append({"ingredient": ingredient, "score": score})

        return self._format_result(found_issues)

    def _format_result(self, issues: list) -> dict:
        if not issues:
            return {"status": "GREEN", "message": "🟢 **Kodlar bazadan topilmadi**\n(Tarkibni o'zingiz ham ko'zdan kechiring)."}
        
        # Saralash
        issues.sort(key=lambda x: x['ingredient'].risk_level, reverse=True)
        
        has_harom = any(x['ingredient'].status == "HAROM" for x in issues)
        has_shubhali = any(x['ingredient'].status == "SHUBHALI" for x in issues)
        
        if has_harom:
            main_msg = "🔴 **DIQQAT! HAROM MODDA TOPILDI.**"
            status = "RED"
        elif has_shubhali:
            main_msg = "🟡 **EHTIYOT BO'LING! Shubha bor.**"
            status = "YELLOW"
        else:
            main_msg = "🟢 **Xavfli kodlar yo'q.** (Barchasi Halol)"
            status = "GREEN"

        return {"status": status, "message": main_msg, "details": issues}
