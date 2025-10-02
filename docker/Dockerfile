# Use the official Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependencies file first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY scripts/ scripts/
COPY data/ data/

# Set the default command to run the scraper
CMD ["python", "scripts/scraper.py"]
