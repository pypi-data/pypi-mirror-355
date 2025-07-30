#!/bin/bash
# author: shadow shell

# chmod 700 uploadtest.sh

python3 -m twine upload --repository testpypi dist/*

# 需要配置 ~.pypirc 文件
#[testpypi]
#  username = __token__
#  password = [your token]

