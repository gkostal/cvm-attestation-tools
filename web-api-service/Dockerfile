FROM ubuntu:24.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update, upgrade, and install required packages
RUN apt update && \
    apt upgrade -y && \
    apt install -y \
        git \
        tpm2-tools \
        python3 \
        python3-pip \
        python3.12-venv \
        sudo && \
    apt clean

# Create a virtual environment
RUN python3 -m venv /opt/venv

# Activate virtual environment and upgrade pip
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip

# Set working directory
WORKDIR /app/src

# Clone the repository and checkout the specific branch
RUN git clone https://github.com/gkostal/cvm-attestation-tools.git && \
    cd cvm-attestation-tools && \
    git fetch --all && \
    git checkout dev/gkostal/web-api-service

# Set working directory to web-api-service
WORKDIR /app/src/cvm-attestation-tools/web-api-service

# Install Python dependencies
RUN pip install -r requirements.txt

# Default shell
CMD ["bash"]
