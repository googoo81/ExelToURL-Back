FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    python3-dev \
    build-essential \
    libcairo2 \
    libcairo2-dev \
    pkg-config \
    libgirepository1.0-dev \
    gir1.2-pango-1.0
