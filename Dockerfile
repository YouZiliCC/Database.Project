FROM ubuntu:24.04

WORKDIR /root

# 替换为国内镜像源（清华）并安装依赖
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|https://mirrors.tuna.tsinghua.edu.cn/ubuntu/|g' /etc/apt/sources.list.d/ubuntu.sources \
    && sed -i 's|http://security.ubuntu.com/ubuntu/|https://mirrors.tuna.tsinghua.edu.cn/ubuntu/|g' /etc/apt/sources.list.d/ubuntu.sources \
    && apt-get update -o Acquire::Retries=3 \
    && apt-get install -y --no-install-recommends curl git pipx \
    && rm -rf /var/lib/apt/lists/*

RUN pipx install uv
RUN curl -o miniconda.sh https://mirrors.pku.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh

ENV TZ=Asia/Shanghai