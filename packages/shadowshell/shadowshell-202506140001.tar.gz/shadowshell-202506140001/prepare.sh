#!/bin/bash
# author: shadowshell

# chmod 700 prepare.sh

# 创建虚拟环境（不重复创建）
if [ -d "venv" ] && [ -f "venv/pyvenv.cfg" ]; then
    echo "Virtual environment exists..."
else
    echo "Creating new virtual environment..."
    python3 -m venv venv
fi

# 进入虚拟环境
source venv/bin/activate

# 安装或升级依赖
pip3 install -r ./requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com 

