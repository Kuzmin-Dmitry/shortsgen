FROM python:3.12-slim

# Install system dependencies including ffmpeg for video processing and font utilities
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    fonts-liberation \
    fonts-dejavu \
    fonts-freefont-ttf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# List all installed fonts for verification during build (with visibility improvements)
RUN ls -la /usr/share/fonts/truetype/liberation && \
    ls -la /usr/share/fonts/truetype/dejavu && \
    ls -la /usr/share/fonts/truetype/freefont

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create output directories
RUN mkdir -p output/images output/video output/voice output/text

# Set environment variable
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "main.py"]
