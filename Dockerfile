FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed for some packages (xgboost, builds)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libgomp1 \
    git \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Copy both requirement files (if present). Docker will prefer the real requirements.txt
# if present and non-empty; otherwise it will fall back to requirements.example.txt.
COPY requirements.example.txt /tmp/requirements.example.txt
COPY requirements.txt /tmp/requirements.txt

RUN if [ -s /tmp/requirements.txt ]; then cp /tmp/requirements.txt /app/requirements.txt; \
    else cp /tmp/requirements.example.txt /app/requirements.txt; fi

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy project files
COPY . /app

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
