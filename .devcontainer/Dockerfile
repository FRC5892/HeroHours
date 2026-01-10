# HeroHours Development Container Configuration
FROM mcr.microsoft.com/devcontainers/base:alpine-3.22

# Install Python and required packages for venv
RUN apk add --no-cache \
    python3 \
    py3-pip \
    python3-dev \
    build-base

# Create symbolic link for python if needed
RUN ln -sf /usr/bin/python3 /usr/local/bin/python

# Install system dependencies (Alpine equivalents)
RUN apk add --no-cache \
    postgresql-client \
    git \
    curl

# Set working directory
WORKDIR /workspace

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=HeroHoursRemake.settings

# Default command
CMD ["python3", "app.py"]