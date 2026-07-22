FROM python:3.11-slim

WORKDIR /app

# Runtime libs mediapipe/opencv need that aren't in the slim base image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Most hosts (Render, Railway, Cloud Run) inject PORT at runtime.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn face_analyzer.api.app:app --host 0.0.0.0 --port ${PORT}"]
