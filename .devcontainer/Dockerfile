FROM mcr.microsoft.com/devcontainers/cpp:1-ubuntu-24.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        clang-format \
        clang-tidy \
        cmake \
        cppcheck \
        curl \
        gdb \
        git \
        gnupg \
        lsb-release \
        ninja-build \
        pkg-config \
    && curl -fsSL https://packages.osrfoundation.org/gazebo.gpg \
        -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
        > /etc/apt/sources.list.d/gazebo-stable.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends gz-harmonic \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV CC=gcc \
    CXX=g++ \
    GZ_VERSION=harmonic
