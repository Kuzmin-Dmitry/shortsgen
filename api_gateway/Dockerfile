FROM python:3.12-slim

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
# Copy application files
COPY . .

# Set ownership for the entire application directory
RUN chown -R ${APP_USER}:${APP_USER} ${APP_HOME} && \
    find ${APP_HOME} -type d -exec chmod 755 {} \; && \
    find ${APP_HOME} -type f -exec chmod 644 {} \;

# =========================================================================
# Runtime configuration
# =========================================================================
# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="${APP_HOME}:${PATH}"

# Switch to non-root user
USER ${APP_USER}

# Expose the API port
EXPOSE 8000

# Add health check to monitor application status
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
