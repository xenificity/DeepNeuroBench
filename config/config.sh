#!/usr/bin/env bash

echo "🥸 Installing Docker, Docker Image, Nextflow, Nvidia-Cuda-drivers, Nextflow and more"
UBUNTU_VERSION="ubuntu2004"
PARABRICKS="nvcr.io/nvidia/clara/clara-parabricks:4.2.1-1"
sudo apt-get -q update
ARCHITECTURE='x86_64'

echo "👉 Installing CUDA for "$UBUNTU_VERSION"."
wget https://developer.download.nvidia.com/compute/cuda/repos/$UBUNTU_VERSION/$ARCHITECTURE/cuda-$UBUNTU_VERSION.pin
sudo mv cuda-$UBUNTU_VERSION.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.0.0/local_installers/cuda-repo-$UBUNTU_VERSION-12-0-local_12.0.0-525.60.13-1_amd64.deb
sudo dpkg -i cuda-repo-$UBUNTU_VERSION-12-0-local_12.0.0-525.60.13-1_amd64.deb
sudo cp /var/cuda-repo-$UBUNTU_VERSION-12-0-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
rm cuda*deb
sudo DEBIAN_FRONTEND=noninteractive apt-get -y install cuda

echo "👉 Installing Docker, nvidia-docker2."
curl https://get.docker.com | sh \
          && sudo systemctl --now enable docker
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
           && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \
              && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nvidia-docker2
# sudo systemctl restart docker
# sudo systemctl status docker

echo "👉 Installing Docker DeepPrep Image."
# sudo docker run hello-world
sudo docker pull pbfslab/deepprep:25.1.0

echo "👉 Installing Java 17"
sudo mkdir -p /usr/lib/jvm
cd /usr/lib/jvm
sudo mkdir -p /mydata
sudo chown ubuntu:ubuntu /mydata
sudo chmod 700 -R /mydata
sudo wget https://download.oracle.com/java/17/archive/jdk-17_linux-x64_bin.tar.gz
sudo tar -xzvf jdk-17_linux-x64_bin.tar.gz
sudo rm jdk-17*.gz
sudo echo "export JAVA_HOME=/usr/lib/jvm/jdk-17" >> ~/.bashrc
sudo echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> ~/.bashrc
source ~/.bashrc

echo "👉 Installing Nextflow"
cd ~
curl -sL https://github.com/nextflow-io/nextflow/releases/download/v24.10.3/nextflow -o nextflow
chmod +x nextflow
sudo mv nextflow /usr/local/bin/

