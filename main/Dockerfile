# Base image (lightweight Linux + build tools)
FROM ubuntu:22.04

# Avoid user input prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install compilers & runtimes
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    g++ \
    openjdk-17-jdk \
    nodejs npm \
    && apt-get clean

# Create a sandbox folder
RUN mkdir /sandbox
WORKDIR /sandbox

# Set default command (can be overridden)
CMD ["bash"]
