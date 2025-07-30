#!/bin/bash
# author: shadow shell

# chmod 700 firetest.sh

# build
rm -rf ./dist/* & python3 -m build

# upload
python3 -m twine upload --repository testpypi dist/*

# install
python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps shadowshell --upgrade