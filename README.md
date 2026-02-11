# 🕌 Halal Helper Bot

### 🌟 Your personal assistant for checking Halal ingredients.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Aiogram](https://img.shields.io/badge/Aiogram-Framework-blueviolet?style=for-the-badge&logo=telegram&logoColor=white)

## 📖 About The Project

**Halal Helper Bot** is a Telegram bot designed to help Muslims easily check food additives (E-codes) and ingredients. The main goal is to make daily shopping easier and ensure that the products consumed are Halal.

> "Consume what is lawful and good."

## ✨ Key Features

* 🔍 **E-Code Checker:** Instantly check if an additive (e.g., E120, E471) is Halal, Haram, or Mushbooh (Doubtful).
* ⚡ **Fast & Simple:** Just send the code, and the bot responds immediately.
* 📜 **Database:** Uses a reliable list of verified food additives.
* 🇺🇿 **Language Support:** Currently supports Uzbek (English coming soon).

## 🛠️ Built With

* **Python** - Core logic and backend.
* **Aiogram** - Asynchronous framework for Telegram Bot API.
* **SQLite / JSON** - For storing data (Simple & Efficient).

## 🚀 How It Works (Logic)

1.  User sends an **E-code** (e.g., `E120`).
2.  The bot searches the code in its database using `if/else` logic or `Dictionary` lookup.
3.  It returns the status:
    * ✅ **Halal** (Safe to eat)
    * ❌ **Haram** (Avoid it)
    * ❓ **Mushbooh** (Need to check source)

## 🔮 Future Plans

- [ ] Add **Barcode Scanner** feature.
- [ ] Add **Prayer Times** & Qibla direction.
- [ ] Include a list of **Halal Restaurants** in Tashkent.
- [ ] Multi-language support (English/Russian).

## 👨‍💻 Author

**Abdusobir Mukhidov**
* GitHub: [@mukhidov02](https://github.com/mukhidov02)
* Telegram: [@mukhidov02](https://t.me/mukhidov02)
* LinkedIn: [Abdusobir Mukhidov](https://linkedin.com/in/mukhidov02)

---
⭐️ **If you like this project, please give it a Star!**
