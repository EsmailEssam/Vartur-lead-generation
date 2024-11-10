# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables to avoid certain warnings
ENV PYTHONUNBUFFERED 1
ENV DISPLAY=:99

# Install system dependencies required by selenium and the browser
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    wget \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Firefox and GeckoDriver
RUN wget -q -O - https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz | tar -xz -C /usr/local/bin

# Set up working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8501 for the Streamlit app
EXPOSE 8501

# Start the app using streamlit
CMD ["streamlit", "run", "main.py"]
