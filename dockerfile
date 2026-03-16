# Use official Python image with build tools
FROM python:3.10-slim-buster

# Install system dependencies required for dlib compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libx11-dev \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port (Render uses 10000 by default)
EXPOSE 10000

# Command to run the application
CMD gunicorn app:app --bind 0.0.0.0:$PORT
