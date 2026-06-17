FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    libnss3 libnspr4 libasound2t64 libcups2t64 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \
    libatspi2.0-0t64 libgtk-3-0t64 \
    libxshmfence1 libegl1 libxcursor1 libgles2 \
    libglib2.0-0t64 libdbus-1-3 \
    libatk1.0-0t64 libatk-bridge2.0-0t64 \
    libx11-6 libxcb1 libxext6 \
    fonts-dejavu-core fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (sin --with-deps, las librerias ya estan via apt)
RUN playwright install chromium

COPY . .

EXPOSE 8090

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]
