FROM ubuntu:24.04

WORKDIR /root
RUN apt update && apt install -y curl git
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN curl -o miniconda.sh https://mirrors.pku.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh

ENV TZ=Asia/Shanghai