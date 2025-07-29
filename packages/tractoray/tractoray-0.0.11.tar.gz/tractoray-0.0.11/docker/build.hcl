target "jammy_python_sys" {
  platforms = ["linux/amd64"]
  dockerfile-inline = <<EOT
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    python3 -m pip install --upgrade pip
EOT
}

target "base" {
  platforms = ["linux/amd64"]
  contexts = {
    base_image = "target:jammy_python_sys"
  }
  context = "${PROJECT_ROOT}"
  tags = [
    "${DOCKER_REPO}/tractoray/base:${DOCKER_TAG}"
  ]
  dockerfile-inline = <<EOT
FROM base_image

RUN apt install wget git net-tools telnet socat --yes
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb \
    && dpkg -i cuda-keyring_1.1-1_all.deb \
    && apt-get update \
    && apt-get -y install cuda-toolkit-12-4 --yes
ENV PATH=/usr/local/cuda-12.4/bin:$PATH
ENV CUDA_HOME=/usr/local/cuda-12.4

RUN apt-get install autoconf libtool libibverbs-dev -y

RUN apt-get install autoconf libtool libibverbs-dev \
    && git clone https://github.com/Mellanox/nccl-rdma-sharp-plugins.git \
    && cd nccl-rdma-sharp-plugins \
    && ./autogen.sh \
    && ./configure --with-cuda=/usr/local/cuda \
    && make -j 16 \
    && make install
EOT
}

target "default" {
  platforms = ["linux/amd64"]
  contexts = {
    base_image = "target:base"
  }
  context = "${PROJECT_ROOT}"
  tags = [
    "${DOCKER_REPO}/tractoray/default:${DOCKER_TAG}"
  ]
  dockerfile-inline = <<EOT
FROM base_image

RUN mkdir /src
COPY ./ /src

RUN pip install poetry==2.1.1 poetry-core==2.1.1 && poetry config virtualenvs.create false

RUN cd /src && poetry install --with ray
EOT
}

target "slim_tests" {
  platforms = ["linux/amd64"]
  contexts = {
    base_image = "target:jammy_python_sys"
  }
  context = "${PROJECT_ROOT}"
  tags = [
    "${DOCKER_REPO}/tractoray/slim_tests:${DOCKER_TAG}"
  ]
  dockerfile-inline = <<EOT
FROM base_image

RUN mkdir /src
COPY ./ /src

RUN apt install socat --yes

RUN pip install poetry==2.1.1 poetry-core==2.1.1 && poetry config virtualenvs.create false

RUN cd /src \
  && pip install poetry-plugin-export \
  && poetry export --with=tests --with=ray --without-hashes --format=requirements.txt > requirements.txt \
  && pip install -r requirements.txt
EOT
}
