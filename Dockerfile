FROM python:3.11-slim

# Install Node.js 20
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Build frontend (produces /app/frontend/dist)
COPY frontend ./frontend
RUN cd frontend && npm install && npm run build

# Copy rest of backend
COPY backend ./backend

EXPOSE 8000

CMD cd backend && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
