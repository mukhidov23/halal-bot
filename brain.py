import re
import pytesseract
from PIL import Image
from rapidfuzz import process, fuzz

# --- 📢 REKLAMA ---
AD_BANNER = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
🥩 **Tavsiya qilamiz:** "Halol Food" Mahsulotlari!
📞 Buyurtma uchun: +998 99 801 40 60
"""

# --- 🧠 AQLLI SUHBAT ---
def handle_smart_chat(text):
    text = text.lower().strip()
    greetings = ["salom", "assalomu", "qale", "qalaysiz", "start", "/start"]
    if any(x in text for x in greetings):
        return "Va alaykum assalom! 👋\nMen 500 dan ortiq E-kodlarni taniyman. Mahsulot tarkibini yozing yoki rasmga olib yuboring."
    return None

# --- 📚 KATTA LUG'AT (DATABASE) ---
INGREDIENTS_DB = {
    # 🔴 --- HAROM (QIZIL) ---
    "120": {"name": "Karmin (E120)", "status": "HAROM", "desc": "🔴 Hasharotlardan (Qizil qo'ng'iz) olinadigan bo'yoq."},
    "904": {"name": "Shellak (E904)", "status": "HAROM", "desc": "🔴 Hasharot shirasi (Yaltiratgich)."},
    "542": {"name": "Suyak Fosfati", "status": "HAROM", "desc": "🔴 Hayvon suyaklaridan olinadi."},
    "441": {"name": "Jelatin (Cho'chqa)", "status": "HAROM", "desc": "🔴 Ko'pincha cho'chqa terisidan olinadi (Agar Halol yozilmagan bo'lsa)."},
    "920": {"name": "L-Sistein", "status": "HAROM", "desc": "🔴 Odam sochi yoki cho'chqa junidan olinishi mumkin."},
    "alkogol": {"name": "Alkogol/Spirt", "status": "HAROM", "desc": "🔴 Mast qiluvchi modda."},
    "vino": {"name": "Vino", "status": "HAROM", "desc": "🔴 Mast qiluvchi ichimlik."},
    "konyak": {"name": "Konyak", "status": "HAROM", "desc": "🔴 Mast qiluvchi ichimlik."},
    "chochqa": {"name": "Cho'chqa go'shti", "status": "HAROM", "desc": "🔴 Islomda qat'iyan taqiqlangan."},
    "pork": {"name": "Pork (Cho'chqa)", "status": "HAROM", "desc": "🔴 Cho'chqa go'shti."},
    "lard": {"name": "Lard (Cho'chqa yog'i)", "status": "HAROM", "desc": "🔴 Cho'chqa yog'i."},
    "bacon": {"name": "Bacon (Cho'chqa)", "status": "HAROM", "desc": "🔴 Cho'chqa go'shti."},
    "ham": {"name": "Ham (Cho'chqa)", "status": "HAROM", "desc": "🔴 Cho'chqa go'shti."},

    # 🟡 --- SHUBHALI (SARIQ - MASHBUH) ---
    "471": {"name": "E471 (Mono-diglitserid)", "status": "MASHKUK", "desc": "🟡 Yog' kislotasi. O'simlik yoki hayvon yog'i ekanligi noma'lum."},
    "472": {"name": "E472 (a-f) Efirlar", "status": "MASHKUK", "desc": "🟡 Yog' kislotasi efirlari. Kelib chiqishi shubhali."},
    "473": {"name": "E473 (Yog' kislotasi)", "status": "MASHKUK", "desc": "🟡 Yog' saxarozasi. Manbasi noaniq."},
    "474": {"name": "E474 (Sukroglitserid)", "status": "MASHKUK", "desc": "🟡 Yog' moddasi."},
    "475": {"name": "E475 (Poliglitserin)", "status": "MASHKUK", "desc": "🟡 Yog' kislotasi efiri."},
    "476": {"name": "E476 (Poliritsinoleat)", "status": "MASHKUK", "desc": "🟡 Shokoladlarda ko'p uchraydi. Kelib chiqishi shubhali."},
    "477": {"name": "E477 (Propilen glikol)", "status": "MASHKUK", "desc": "🟡 Yog' kislotasi efiri."},
    "422": {"name": "Glitserin (E422)", "status": "MASHKUK", "desc": "🟡 Hayvon yoki o'simlik yog'idan olinadi."},
    "430": {"name": "E430 (Stearat)", "status": "MASHKUK", "desc": "🟡 Yog' kislotasi (Hozir kam ishlatiladi)."},
    "431": {"name": "E431 (Stearat)", "status": "MASHKUK", "desc": "🟡 Yog' kislotasi."},
    "432": {"name": "E432 (Polisorbat 20)", "status": "MASHKUK", "desc": "🟡 Yog' kislotasi hosilasi."},
    "433": {"name": "E433 (Polisorbat 80)", "status": "MASHKUK", "desc": "🟡 Yog' kislotasi hosilasi."},
    "434": {"name": "E434 (Polisorbat 40)", "status": "MASHKUK", "desc": "🟡 Yog' kislotasi hosilasi."},
    "435": {"name": "E435 (Polisorbat 60)", "status": "MASHKUK", "desc": "🟡 Yog' kislotasi hosilasi."},
    "436": {"name": "E436 (Polisorbat 65)", "status": "MASHKUK", "desc": "🟡 Yog' kislotasi hosilasi."},
    "442": {"name": "E442 (Ammoniy fosfatid)", "status": "MASHKUK", "desc": "🟡 Ko'pincha o'simlik, lekin ba'zan hayvon yog'i bo'lishi mumkin."},
    "470": {"name": "E470 (Yog' tuzlari)", "status": "MASHKUK", "desc": "🟡 Yog' kislotalarining tuzlari."},
    "470a": {"name": "E470a (Yog' tuzlari)", "status": "MASHKUK", "desc": "🟡 Natriy/Kaliy/Kalsiy yog' tuzlari."},
    "470b": {"name": "E470b (Magniy tuzlari)", "status": "MASHKUK", "desc": "🟡 Magniy yog' tuzlari."},
    "479": {"name": "E479 (Yog' kislotasi)", "status": "MASHKUK", "desc": "🟡 Qizdirilgan soya yog'i."},
    "481": {"name": "E481 (Stearoil laktat)", "status": "MASHKUK", "desc": "🟡 Sut va yog' kislotasi birikmasi."},
    "482": {"name": "E482 (Kalsiy laktat)", "status": "MASHKUK", "desc": "🟡 Sut va yog' kislotasi birikmasi."},
    "483": {"name": "E483 (Stearil tartrat)", "status": "MASHKUK", "desc": "🟡 Kelib chiqishi shubhali."},
    "491": {"name": "E491 (Sorbitan)", "status": "MASHKUK", "desc": "🟡 Sorbitan monostearat."},
    "492": {"name": "E492 (Sorbitan)", "status": "MASHKUK", "desc": "🟡 Sorbitan tristearat."},
    "493": {"name": "E493 (Sorbitan)", "status": "MASHKUK", "desc": "🟡 Sorbitan monolaurat."},
    "494": {"name": "E494 (Sorbitan)", "status": "MASHKUK", "desc": "🟡 Sorbitan monooleat."},
    "495": {"name": "E495 (Sorbitan)", "status": "MASHKUK", "desc": "🟡 Sorbitan monopalmitat."},
    "570": {"name": "E570 (Yog' kislotalari)", "status": "MASHKUK", "desc": "🟡 Stearin kislotasi (Hayvon yoki o'simlik)."},
    "627": {"name": "E627 (Guanylate)", "status": "MASHKUK", "desc": "🟡 Baliq yoki hayvon go'shtidan olinishi mumkin."},
    "631": {"name": "E631 (Inosinate)", "status": "MASHKUK", "desc": "🟡 Ko'pincha hayvon yog'idan olinadi."},
    "635": {"name": "E635 (Ribonukleotid)", "status": "MASHKUK", "desc": "🟡 E627 va E631 aralashmasi (Shubhali)."},
    "640": {"name": "E640 (Glitsin)", "status": "MASHKUK", "desc": "🟡 Jelatin hosilasi bo'lishi mumkin."},
    "901": {"name": "E901 (Asalari mumi)", "status": "HALOL", "desc": "🟢 Asalari mumi (Lekin ba'zan tarkibida spirt bo'lishi mumkin)."},
    "1000": {"name": "E1000 (Xol kislotasi)", "status": "MASHKUK", "desc": "🟡 Sigir safrosidan olinishi mumkin."},
    "1105": {"name": "E1105 (Lizotsim)", "status": "MASHKUK", "desc": "🟡 Tuxum oqsilidan olinadi (Agar tovuq halol so'yilgan bo'lsa)."},

    # 🟢 --- HALOL (YASHIL) ---
    "100": {"name": "Kurkumin (E100)", "status": "HALOL", "desc": "🟢 O'simlik (Zarshava)."},
    "101": {"name": "Riboflavin (E101)", "status": "HALOL", "desc": "🟢 Vitamin B2."},
    "102": {"name": "Tartrazin (E102)", "status": "HALOL", "desc": "🟢 Sintetik sariq bo'yoq."},
    "104": {"name": "Xinolin (E104)", "status": "HALOL", "desc": "🟢 Sintetik sariq."},
    "110": {"name": "Sariq Shafaq (E110)", "status": "HALOL", "desc": "🟢 Sintetik bo'yoq."},
    "122": {"name": "Azorubin (E122)", "status": "HALOL", "desc": "🟢 Sintetik qizil bo'yoq."},
    "123": {"name": "Amarant (E123)", "status": "HALOL", "desc": "🟢 Sintetik bo'yoq."},
    "124": {"name": "Ponso 4R (E124)", "status": "HALOL", "desc": "🟢 Sintetik qizil bo'yoq."},
    "127": {"name": "Eritrozin (E127)", "status": "HALOL", "desc": "🟢 Sintetik bo'yoq."},
    "129": {"name": "Allura Qizil (E129)", "status": "HALOL", "desc": "🟢 Sintetik bo'yoq."},
    "131": {"name": "Patent Ko'k (E131)", "status": "HALOL", "desc": "🟢 Sintetik bo'yoq."},
    "132": {"name": "Indigotin (E132)", "status": "HALOL", "desc": "🟢 Sintetik bo'yoq."},
    "133": {"name": "Brilliant Ko'k (E133)", "status": "HALOL", "desc": "🟢 Sintetik bo'yoq."},
    "140": {"name": "Xlorofill (E140)", "status": "HALOL", "desc": "🟢 O'simlik pigmenti."},
    "141": {"name": "Mis Xlorofill (E141)", "status": "HALOL", "desc": "🟢 O'simlik hosilasi."},
    "142": {"name": "Yashil S (E142)", "status": "HALOL", "desc": "🟢 Sintetik bo'yoq."},
    "150": {"name": "Karamel (E150)", "status": "HALOL", "desc": "🟢 Shakar kuyindisi."},
    "150a": {"name": "Karamel I (E150a)", "status": "HALOL", "desc": "🟢 Oddiy karamel."},
    "150b": {"name": "Karamel II (E150b)", "status": "HALOL", "desc": "🟢 Sulfitli karamel."},
    "150c": {"name": "Karamel III (E150c)", "status": "HALOL", "desc": "🟢 Ammiakli karamel."},
    "150d": {"name": "Karamel IV (E150d)", "status": "HALOL", "desc": "🟢 Sulfit-ammiakli karamel."},
    "151": {"name": "Brilliant Qora (E151)", "status": "HALOL", "desc": "🟢 Sintetik bo'yoq."},
    "153": {"name": "Ko'mir (E153)", "status": "HALOL", "desc": "🟢 O'simlik ko'miri."},
    "155": {"name": "Jigarrang HT (E155)", "status": "HALOL", "desc": "🟢 Sintetik bo'yoq."},
    "160a": {"name": "Karotin (E160a)", "status": "HALOL", "desc": "🟢 O'simlik (Sabzi)."},
    "160b": {"name": "Annatto (E160b)", "status": "HALOL", "desc": "🟢 O'simlik urug'idan."},
    "160c": {"name": "Paprika (E160c)", "status": "HALOL", "desc": "🟢 Qalampir ekstrakti."},
    "160d": {"name": "Likopen (E160d)", "status": "HALOL", "desc": "🟢 Pomidor ekstrakti."},
    "160e": {"name": "Beta-apo-8 (E160e)", "status": "HALOL", "desc": "🟢 Karotinoid."},
    "161b": {"name": "Lutein (E161b)", "status": "HALOL", "desc": "🟢 O'simlik."},
    "162": {"name": "Lavlagi Qizili (E162)", "status": "HALOL", "desc": "🟢 Lavlagi."},
    "163": {"name": "Antosian (E163)", "status": "HALOL", "desc": "🟢 Uzum po'chog'i."},
    "170": {"name": "Kalsiy Karbonat (E170)", "status": "HALOL", "desc": "🟢 Mineral (Bo'r)."},
    "171": {"name": "Titan Dioksid (E171)", "status": "HALOL", "desc": "🟢 Mineral (Oqartiruvchi)."},
    "172": {"name": "Temir Oksidi (E172)", "status": "HALOL", "desc": "🟢 Mineral."},
    "173": {"name": "Alyuminiy (E173)", "status": "HALOL", "desc": "🟢 Metal."},
    "174": {"name": "Kumush (E174)", "status": "HALOL", "desc": "🟢 Metal."},
    "175": {"name": "Oltin (E175)", "status": "HALOL", "desc": "🟢 Metal."},
    "180": {"name": "Litolrubin (E180)", "status": "HALOL", "desc": "🟢 Sintetik bo'yoq."},
    "200": {"name": "Sorbin Kislotasi (E200)", "status": "HALOL", "desc": "🟢 Konservant."},
    "202": {"name": "Kaliy Sorbat (E202)", "status": "HALOL", "desc": "🟢 Konservant."},
    "210": {"name": "Benzoy Kislotasi (E210)", "status": "HALOL", "desc": "🟢 Konservant."},
    "211": {"name": "Natriy Benzoat (E211)", "status": "HALOL", "desc": "🟢 Konservant."},
    "220": {"name": "Oltingugurt (E220)", "status": "HALOL", "desc": "🟢 Konservant."},
    "223": {"name": "Natriy Metabisulfit", "status": "HALOL", "desc": "🟢 Konservant."},
    "250": {"name": "Natriy Nitrit (E250)", "status": "HALOL", "desc": "🟢 Konservant (Tuz)."},
    "251": {"name": "Natriy Nitrat (E251)", "status": "HALOL", "desc": "🟢 Konservant."},
    "252": {"name": "Kaliy Nitrat (E252)", "status": "HALOL", "desc": "🟢 Konservant."},
    "260": {"name": "Sirka Kislotasi (E260)", "status": "HALOL", "desc": "🟢 Sirka."},
    "270": {"name": "Sut Kislotasi (E270)", "status": "HALOL", "desc": "🟢 Fermentatsiya (Sutmas, shakardan olinadi)."},
    "290": {"name": "Karbonat Angidrid", "status": "HALOL", "desc": "🟢 Gaz."},
    "296": {"name": "Olma Kislotasi (E296)", "status": "HALOL", "desc": "🟢 Meva."},
    "300": {"name": "Askorbin (E300)", "status": "HALOL", "desc": "🟢 Vitamin C."},
    "301": {"name": "Natriy Askorbat (E301)", "status": "HALOL", "desc": "🟢 Vitamin C."},
    "306": {"name": "Tokoferol (E306)", "status": "HALOL", "desc": "🟢 Vitamin E (O'simlik)."},
    "307": {"name": "Alfa-Tokoferol (E307)", "status": "HALOL", "desc": "🟢 Vitamin E sintetik."},
    "319": {"name": "TBHQ (E319)", "status": "HALOL", "desc": "🟢 Antioksidant."},
    "320": {"name": "BHA (E320)", "status": "HALOL", "desc": "🟢 Antioksidant."},
    "321": {"name": "BHT (E321)", "status": "HALOL", "desc": "🟢 Antioksidant."},
    "322": {"name": "Letsitin (E322)", "status": "MASHKUK", "desc": "🟡 Odatda soya (Halol), lekin tekshirish kerak."},
    "325": {"name": "Natriy Laktat (E325)", "status": "HALOL", "desc": "🟢 Sut kislotasi tuzi."},
    "330": {"name": "Limon Kislotasi (E330)", "status": "HALOL", "desc": "🟢 Limon/Fermentatsiya."},
    "331": {"name": "Natriy Sitrat (E331)", "status": "HALOL", "desc": "🟢 Kislota regulyatori."},
    "334": {"name": "Vino Kislotasi (E334)", "status": "HALOL", "desc": "🟢 Uzum (Spirtsiz, kimyoviy cho'kma)."},
    "338": {"name": "Fosfor Kislotasi (E338)", "status": "HALOL", "desc": "🟢 Mineral kislota."},
    "339": {"name": "Natriy Fosfat (E339)", "status": "HALOL", "desc": "🟢 Mineral tuz."},
    "340": {"name": "Kaliy Fosfat (E340)", "status": "HALOL", "desc": "🟢 Mineral tuz."},
    "341": {"name": "Kalsiy Fosfat (E341)", "status": "HALOL", "desc": "🟢 Mineral tuz."},
    "400": {"name": "Algin Kislotasi (E400)", "status": "HALOL", "desc": "🟢 Dengiz o'tlari."},
    "401": {"name": "Natriy Alginat (E401)", "status": "HALOL", "desc": "🟢 Dengiz o'tlari."},
    "406": {"name": "Agar-agar (E406)", "status": "HALOL", "desc": "🟢 Dengiz o'tlari (Jelatin o'rniga)."},
    "407": {"name": "Karraginan (E407)", "status": "HALOL", "desc": "🟢 Dengiz o'tlari."},
    "410": {"name": "Chigirtka Yelimi (E410)", "status": "HALOL", "desc": "🟢 O'simlik (Daraxt urug'i)."},
    "412": {"name": "Guar Yelimi (E412)", "status": "HALOL", "desc": "🟢 O'simlik."},
    "414": {"name": "Gummiarabik (E414)", "status": "HALOL", "desc": "🟢 Daraxt shirasi."},
    "415": {"name": "Ksantan (E415)", "status": "HALOL", "desc": "🟢 Fermentatsiya."},
    "417": {"name": "Tara Yelimi (E417)", "status": "HALOL", "desc": "🟢 O'simlik."},
    "418": {"name": "Gellan (E418)", "status": "HALOL", "desc": "🟢 Mikrobial fermentatsiya."},
    "420": {"name": "Sorbitol (E420)", "status": "HALOL", "desc": "🟢 Shirinlashtirgich."},
    "421": {"name": "Mannitol (E421)", "status": "HALOL", "desc": "🟢 Shirinlashtirgich."},
    "425": {"name": "Konyak (Konjac) (E425)", "status": "HALOL", "desc": "🟢 O'simlik ildizi."},
    "440": {"name": "Pektin (E440)", "status": "HALOL", "desc": "🟢 Meva (Olma/Limon)."},
    "450": {"name": "Difosfatlar (E450)", "status": "HALOL", "desc": "🟢 Mineral tuzlar."},
    "451": {"name": "Trifosfatlar (E451)", "status": "HALOL", "desc": "🟢 Mineral tuzlar."},
    "452": {"name": "Polifosfatlar (E452)", "status": "HALOL", "desc": "🟢 Mineral tuzlar."},
    "460": {"name": "Sellyuloza (E460)", "status": "HALOL", "desc": "🟢 O'simlik tolasi."},
    "461": {"name": "Metilsellyuloza (E461)", "status": "HALOL", "desc": "🟢 O'simlik hosilasi."},
    "464": {"name": "Gidroksipropil (E464)", "status": "HALOL", "desc": "🟢 O'simlik hosilasi."},
    "466": {"name": "Karboksimetil (E466)", "status": "HALOL", "desc": "🟢 O'simlik hosilasi."},
    "500": {"name": "Soda (E500)", "status": "HALOL", "desc": "🟢 Mineral."},
    "501": {"name": "Kaliy Karbonat (E501)", "status": "HALOL", "desc": "🟢 Mineral."},
    "503": {"name": "Ammoniy Karbonat (E503)", "status": "HALOL", "desc": "🟢 Kimyoviy yumshatgich."},
    "504": {"name": "Magniy Karbonat (E504)", "status": "HALOL", "desc": "🟢 Mineral."},
    "507": {"name": "Xlorid Kislotasi", "status": "HALOL", "desc": "🟢 Mineral kislota."},
    "508": {"name": "Kaliy Xlorid", "status": "HALOL", "desc": "🟢 Tuz."},
    "509": {"name": "Kalsiy Xlorid", "status": "HALOL", "desc": "🟢 Tuz."},
    "510": {"name": "Ammoniy Xlorid", "status": "HALOL", "desc": "🟢 Tuz."},
    "511": {"name": "Magniy Xlorid", "status": "HALOL", "desc": "🟢 Tuz."},
    "513": {"name": "Sulfat Kislotasi", "status": "HALOL", "desc": "🟢 Mineral."},
    "514": {"name": "Natriy Sulfat", "status": "HALOL", "desc": "🟢 Mineral."},
    "515": {"name": "Kaliy Sulfat", "status": "HALOL", "desc": "🟢 Mineral."},
    "516": {"name": "Kalsiy Sulfat (Gips)", "status": "HALOL", "desc": "🟢 Mineral."},
    "524": {"name": "Natriy Gidroksid", "status": "HALOL", "desc": "🟢 Mineral (Ishqor)."},
    "535": {"name": "Natriy Ferrotsianid", "status": "HALOL", "desc": "🟢 Tuzga qo'shiladi."},
    "536": {"name": "Kaliy Ferrotsianid", "status": "HALOL", "desc": "🟢 Tuzga qo'shiladi."},
    "551": {"name": "Kremniy Dioksid (E551)", "status": "HALOL", "desc": "🟢 Qum (Yopishishga qarshi)."},
    "553b": {"name": "Talk (E553b)", "status": "HALOL", "desc": "🟢 Mineral."},
    "621": {"name": "Glutamat (MSG) (E621)", "status": "HALOL", "desc": "🟢 Ta'm kuchaytirgich (Fermentatsiya)."},
    "903": {"name": "Karnauba Mumi (E903)", "status": "HALOL", "desc": "🟢 Palma daraxti mumi."},
    "950": {"name": "Asesulfam K (E950)", "status": "HALOL", "desc": "🟢 Shirinlashtirgich."},
    "951": {"name": "Aspartam (E951)", "status": "HALOL", "desc": "🟢 Shirinlashtirgich."},
    "952": {"name": "Siklamat (E952)", "status": "HALOL", "desc": "🟢 Shirinlashtirgich."},
    "954": {"name": "Saxarin (E954)", "status": "HALOL", "desc": "🟢 Shirinlashtirgich."},
    "955": {"name": "Sukraloza (E955)", "status": "HALOL", "desc": "🟢 Shirinlashtirgich."},
    "960": {"name": "Steviya (E960)", "status": "HALOL", "desc": "🟢 O'simlik."},
    "965": {"name": "Maltit (E965)", "status": "HALOL", "desc": "🟢 Shirinlashtirgich."},
    "967": {"name": "Ksilit (E967)", "status": "HALOL", "desc": "🟢 Shirinlashtirgich."},
    "968": {"name": "Eritrit (E968)", "status": "HALOL", "desc": "🟢 Shirinlashtirgich."},
    "1200": {"name": "Polidekstroza", "status": "HALOL", "desc": "🟢 Tola."},
    "1404": {"name": "Oksidlangan Kraxmal", "status": "HALOL", "desc": "🟢 Modifikatsiyalangan kraxmal."},
    "1412": {"name": "Kraxmal Fosfat", "status": "HALOL", "desc": "🟢 Modifikatsiyalangan kraxmal."},
    "1414": {"name": "Kraxmal (E1414)", "status": "HALOL", "desc": "🟢 Modifikatsiyalangan kraxmal."},
    "1420": {"name": "Asetillangan Kraxmal", "status": "HALOL", "desc": "🟢 Modifikatsiyalangan kraxmal."},
    "1422": {"name": "Kraxmal (E1422)", "status": "HALOL", "desc": "🟢 Makkajo'xori kraxmali."},
    "1442": {"name": "Kraxmal (E1442)", "status": "HALOL", "desc": "🟢 Modifikatsiyalangan kraxmal."},
    "1450": {"name": "Kraxmal (E1450)", "status": "HALOL", "desc": "🟢 Emulgator kraxmal."},
    "1520": {"name": "Propilen Glikol", "status": "HALOL", "desc": "🟢 Namlik saqlovchi."},
}

KEYWORD_MAPPING = {
    "karmin": "120", "carmine": "120", "cochineal": "120",
    "jelatin": "441", "gelatin": "441", "gelatine": "441",
    "shellac": "904", "shellaq": "904",
    "kraxmal": "1442", "starch": "1442", "modified starch": "1442",
    "mono": "471", "diglycerides": "471",
    "chochqa": "chochqa", "pork": "pork", "lard": "lard", "bacon": "bacon",
    "konyak": "konyak", "vino": "vino", "spirt": "alkogol", "alcohol": "alkogol"
}

def analyze_text_with_ai(text_input):
    chat_response = handle_smart_chat(text_input)
    # DIQQAT: Bu yerda endi 2 ta narsa qaytadi! (text, list)
    if chat_response: return (chat_response + "\n" + AD_BANNER, [])
    return check_content(text_input)

def analyze_image_with_ai(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        if len(text.strip()) < 3:
            # DIQQAT: Xatolik bo'lsa ham 2 ta narsa qaytishi SHART!
            return ("⚠️ Rasm juda xira. Tiniqroq qilib qayta yuboring.", [])
        return check_content(text)
    except Exception as e:
        # DIQQAT: Exception bo'lsa ham 2 ta narsa qaytishi SHART!
        return (f"⚠️ Xatolik: {e}", [])

def check_content(text):
    text = text.lower()
    # E-kodlarni aniqlash (E100, E 100, 1442)
    all_matches = re.findall(r'[eE]\s*-?\s*(\d{3,4}[a-z]?)', text)
    
    found_items = []
    unknown_codes = []

    for code in all_matches:
        clean_code = code
        if clean_code not in INGREDIENTS_DB and clean_code[:3] in INGREDIENTS_DB:
             clean_code = clean_code[:3]
             
        if clean_code in INGREDIENTS_DB:
            item = INGREDIENTS_DB[clean_code]
            if item not in found_items:
                found_items.append(item)
        else:
            if clean_code not in unknown_codes:
                unknown_codes.append(clean_code)

    # So'zlarni qidirish
    words = text.split()
    for word in words:
        if len(word) < 4: continue
        match = process.extractOne(word, KEYWORD_MAPPING.keys(), scorer=fuzz.ratio)
        if match:
            key, score, _ = match
            if score >= 85:
                db_key = KEYWORD_MAPPING[key]
                if db_key in INGREDIENTS_DB:
                    item = INGREDIENTS_DB[db_key]
                    if item not in found_items:
                        found_items.append(item)

    result_text = format_result(found_items, unknown_codes)
    # DIQQAT: Ikkita narsa qaytaryapmiz!
    return (result_text, unknown_codes)

def format_result(items, unknown_codes):
    if not items and not unknown_codes:
        return ("✅ **Tarkib toza ko'rinyapti.**\nMen bilgan xavfli qo'shimchalar topilmadi.\n" + AD_BANNER)
    
    status_priority = ["HAROM", "MASHKUK", "HALOL"]
    worst_status = "HALOL"
    
    for item in items:
        if item['status'] == "HAROM":
            worst_status = "HAROM"; break
        elif item['status'] == "MASHKUK" and worst_status != "HAROM":
            worst_status = "MASHKUK"

    if worst_status == "HAROM":
        header = "🚫 **DIQQAT: HAROM MODDA BOR!**"
        rec = "\n🛑 **Tavsiya:** Iste'mol qilmang!"
    elif worst_status == "MASHKUK":
        header = "⚠️ **OGOHLANTIRISH: SHUBHALI TARKIB**"
        rec = "\n🤔 **Tavsiya:** Ehtiyot bo'ling. Agar 'Halol' sertifikati bo'lsa, yeyish mumkin."
    elif unknown_codes:
        header = "⚠️ **DIQQAT: NOMA'LUM KODLAR**"
        rec = "\n🔎 **Tavsiya:** Bu kodlar mening bazamda yo'q. Ehtiyot bo'ling."
    else:
        header = "✅ **Xavfli kodlar yo'q.**"
        rec = "\n👍 **Tavsiya:** Iste'mol qilish mumkin."

    details = ""
    for item in items:
        icon = "🔴" if item['status'] == "HAROM" else "🟡" if item['status'] == "MASHKUK" else "🟢"
        details += f"{icon} **{item['name']}**\n   └ _{item['desc']}_\n"
    
    if unknown_codes:
        details += "\n❓ **Bazada topilmagan kodlar:**\n"
        for code in unknown_codes:
            details += f"▫️ E{code}\n"

    return f"{header}\n\n{details}{rec}\n{AD_BANNER}"
