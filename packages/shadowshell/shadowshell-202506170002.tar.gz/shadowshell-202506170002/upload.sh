#!/bin/bash
# author: shadow shell

# chmod 700 upload.sh

python3 -m twine upload dist/*

# 需要配置 ~.pypirc 文件
#[pypi]
#  username = __token__
#  password = [your token]

