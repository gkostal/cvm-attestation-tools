FROM ubuntu:24.04

# Avoid prompts during package operations
ENV DEBIAN_FRONTEND=noninteractive

# Update, upgrade, and install git
RUN apt update && \
    apt upgrade -y && \
    apt install -y git && \
    apt clean

# Default shell
CMD ["bash"]
