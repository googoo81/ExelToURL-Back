FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-dev \
    build-essential \
    libcairo2 \
    libcairo2-dev \
    pkg-config \
    libgirepository1.0-dev \
    gir1.2-pango-1.0 \
    libffi-dev \
    libssl-dev \
    libcurl4-openssl-dev \
    libxml2-dev \
    libxslt1-dev \
    git \
    curl \
    # cairo-related dependencies 추가
    libpangocairo-1.0-0 \
    libpango1.0-dev \
    libatk1.0-dev \
    libgdk-pixbuf2.0-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Copy the rest of your app
COPY . .

# Run with Gunicorn
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000", "--workers=2"]
