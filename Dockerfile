# Python 3.10 versiyasini olamiz
FROM python:3.10-slim

# 1. Tesseract va kerakli tizim kutubxonalarini majburlab o'rnatamiz
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Ishchi papkani belgilaymiz
WORKDIR /app

# 3. Talab qilingan kutubxonalarni o'rnatamiz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Barcha kodlarni serverga ko'chiramiz
COPY . .

# 5. Botni ishga tushiramiz
CMD ["python", "main.py"]
