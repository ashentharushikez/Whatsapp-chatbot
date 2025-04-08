# Use Node.js base image 
FROM node:18

# Set working directory
WORKDIR /app

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the app
COPY . .

# Create .wwebjs_auth directory
RUN mkdir -p /app/.wwebjs_auth

# Expose ports
EXPOSE 3000

# Start the bot
CMD ["node", "index.js"]