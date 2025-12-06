FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./

# Create data directory
RUN mkdir -p data

# Set environment variables (can be overridden)
ENV LOTTERY_DATA_SCRAPER_BUCKET=jackpot-iq
ENV PORT=8080

# Expose the port Cloud Run will use
EXPOSE 8080

# Run the Flask server (listens on PORT env var)
CMD ["python", "main.py"]

