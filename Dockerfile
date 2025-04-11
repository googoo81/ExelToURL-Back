FROM python:3.10-slim

# Install system dependencies (incl. cairo-related for pycairo)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev \
    gcc \
    pkg-config \
    libcairo2 \
    libcairo2-dev \
    libgirepository1.0-dev \
    gir1.2-pango-1.0 \
    libpango1.0-dev \
    libpangocairo-1.0-0 \
    libatk1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    libssl-dev \
    libcurl4-openssl-dev \
    libxml2-dev \
    libxslt1-dev \
    git \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Preinstall pycairo to avoid build issues
RUN pip install --upgrade pip setuptools wheel \
    && pip install pycairo

# Copy requirements and install the rest
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy rest of the app
COPY . .

# Expose port
EXPOSE 5000

# Run with Gunicorn
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000", "--workers=2"]
