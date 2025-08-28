
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System packages:
# - ffmpeg: needed by pydub (and helps with audio conversions)
# - poppler-utils: needed by pdf2image
# - tesseract-ocr: enables OCR fallback (safe even if you don't use it)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Install Python deps first (better cache)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy app code
COPY . .

# Streamlit defaults
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
# If you want to disable CORS/CSRF in specific environments, set via flags below.

# Expose Streamlit port
EXPOSE 8501

# Run the app
# You can add extra flags as needed (e.g., --server.enableCORS=false)
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
