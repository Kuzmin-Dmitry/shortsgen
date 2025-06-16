FROM python:3.12-slim

# =========================================================================
# System dependencies layer
# =========================================================================
# Install essential system dependencies with clear grouping and minimized layers
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Video processing tools
    ffmpeg \
    # Graphics and display libraries
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    # Font packages for text rendering
    fonts-liberation \
    fonts-dejavu \
    fonts-freefont-ttf \
        && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# =========================================================================
# Configuration and environment setup
# =========================================================================
# Define configurable build arguments with defaults
ARG APP_USER=appuser
ARG APP_USER_ID=1000
ARG APP_GROUP_ID=1000
ARG APP_HOME=/app

# Create a non-root user for security
RUN groupadd -g ${APP_GROUP_ID} ${APP_USER} && \
    useradd -u ${APP_USER_ID} -g ${APP_GROUP_ID} -ms /bin/bash ${APP_USER}

# Set working directory
WORKDIR ${APP_HOME}

# =========================================================================
# Application dependencies layer (optimized for caching)
# =========================================================================
# Copy only requirements file first for better layer caching
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =========================================================================
# Application code layer
# =========================================================================
# Copy project files
COPY . .

# Create output directory structure and set permissions
RUN mkdir -p output/scenes output/video output/voice output/text && \
    # Set ownership for the entire application directory
    chown -R ${APP_USER}:${APP_USER} ${APP_HOME} && \
    find ${APP_HOME} -type d -exec chmod 755 {} \; && \
    find ${APP_HOME} -type f -exec chmod 644 {} \; && \
    # Allow group write permissions for output directories
    chmod 775 ${APP_HOME}/output ${APP_HOME}/output/*

# =========================================================================
# Runtime configuration
# =========================================================================
# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="${APP_HOME}:${PATH}"

# Expose the API port
EXPOSE 8001

# Add health check to monitor application status
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
