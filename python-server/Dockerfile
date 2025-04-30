FROM python:3.9-slim

WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create images directory structure
RUN mkdir -p /app/images/phones/samsung && \
    mkdir -p /app/images/phones/apple && \
    mkdir -p /app/images/accessories/chargers && \
    mkdir -p /app/images/accessories/cases

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Start the Flask application
CMD ["python", "bot.py"]