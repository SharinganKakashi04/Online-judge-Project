# oj runner image with C/C++/Python/Java
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates build-essential g++ gcc \
    python3 python3-pip openjdk-17-jdk-headless \
  && rm -rf /var/lib/apt/lists/*
    
# non-root user for safety
RUN useradd -ms /bin/bash runner
USER runner
WORKDIR /sandbox
