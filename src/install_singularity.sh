#!/bin/bash

# Update the package list
sudo apt update

# Install dependencies
sudo apt install -y \
    build-essential \
    libseccomp-dev \
    pkg-config \
    squashfs-tools \
    cryptsetup \
    wget \
    git \
    uuid-dev \
    libgpgme-dev \
    libseccomp-dev \
    libglib2.0-dev \
    libssl-dev \
    python3 \
    python3-pip

# Install Go (required for Singularity)
GO_VERSION=1.20.5
wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz
rm go${GO_VERSION}.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
echo "export PATH=\$PATH:/usr/local/go/bin" >> ~/.bashrc
source ~/.bashrc

# Clone the Singularity repository
SINGULARITY_VERSION=3.8.7
git clone --branch v${SINGULARITY_VERSION} https://github.com/apptainer/singularity.git
cd singularity

# Build and install Singularity
./mconfig
make -C builddir
sudo make -C builddir install

# build .sif image at /mydata
sudo singularity build /mydata/deepprep_25.1.0.sif docker://pbfslab/deepprep:25.1.0

# Verify the installation
singularity --version
