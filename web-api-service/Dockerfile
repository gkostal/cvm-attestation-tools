FROM python:3.12-slim

# Update system packages
RUN apt-get update && apt-get upgrade -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# Update pip and setup tools (avoid S360 issues)
RUN pip install --upgrade pip setuptools

# Main app: web-api-service
WORKDIR /app/web-api-service
COPY web-api-service/. .
RUN pip install --no-cache-dir -r requirements.txt

# Dependency: cvm-attestation
WORKDIR /app/cvm-attestation
COPY cvm-attestation-tools/cvm-attestation/. .

# Expose port
EXPOSE 5000

# Run the application
WORKDIR /app/web-api-service
CMD ["python", "app.py"]
