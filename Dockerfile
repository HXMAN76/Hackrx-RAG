FROM python:3.13-slim


# Set base Python environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=1800

# Set working directory
WORKDIR /app

# Install system dependencies


# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

COPY .env .env

# Create temp directory
RUN mkdir -p /app/app/temp

# Expose FastAPI port
EXPOSE 8000

# Default app launch command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
