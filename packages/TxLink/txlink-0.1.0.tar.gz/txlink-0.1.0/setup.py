# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# 读取README.md文件
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="TxLink",
    version="0.1.0",
    packages=find_packages(),
    author="95ge",
    author_email="litaoflyme@163.com",
    description="TxLink,一个基于python的通信框架,支持多种业务场景模式,广泛应用于分布式量化交易系统构建中",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/95ge/TxLink",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.0",
    install_requires=[],
) 