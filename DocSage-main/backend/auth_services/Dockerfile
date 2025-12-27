# Use Python 3.11 for better performance/security, unless your project requires 3.9
FROM python:3.11-slim

WORKDIR /app

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy application code (after dependencies for Docker cache optimization)
COPY . /app

# (Optional) Copy .env if you want it in the image (not for production)
# COPY .env .env

# Expose the correct port (matching uvicorn)
EXPOSE 8000

# (Optional) Informational environment variable
ENV NAME=AUTHService

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
