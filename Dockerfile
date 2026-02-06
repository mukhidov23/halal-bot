FROM python:3.10-slim

# 1. Kerakli tizim kutubxonalari (Postgres va Tesseract uchun)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 2. Ishchi papka
WORKDIR /app

# 3. Python kutubxonalari
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Kodlar
COPY . .

# 5. Start
CMD ["python", "main.py"]
