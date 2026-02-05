# Yengil Python versiyasini olamiz
FROM python:3.10-slim

# Kerakli tizim kutubxonalarini o'rnatamiz (Tesseract olib tashlandi, gcc qo'shildi)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Ishchi papkani belgilaymiz
WORKDIR /app

# Kutubxonalarni o'rnatamiz
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Kodlarni ko'chiramiz
COPY . .

# Botni ishga tushiramiz
CMD ["python", "main.py"]
