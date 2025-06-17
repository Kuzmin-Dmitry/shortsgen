FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu-core \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /app/output/video /app/output/scenes /app/output/voice

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# Run the application
CMD ["python", "app.py"]
