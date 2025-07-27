# Use the official Python 3.11 slim image as the base
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Upgrade & update, then clean up apt cache to reduce image size
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Copy your project files into the container
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Expose the FastAPI port
EXPOSE 8001

# Optional: Set a name environment variable (can be omitted or customized)
ENV NAME=CONVOService

# Start the FastAPI app using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
