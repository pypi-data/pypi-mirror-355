# -*- coding: utf-8 -*-
"""
Created on 2025/6/13 22:50
@author: guest881
"""
from setuptools import setup, find_packages

setup(
    name="guest881_linkLists",  # 包名，PyPI 上唯一，若已存在需换名（可去 PyPI 搜搜看）
    version="0.1.0",   # 版本号，遵循语义化（如 主版本.次版本.补丁）
    packages=find_packages(),  # 自动发现包（会包含 linkLists 目录）
    description="最基础的链表库，自娱自乐",
    url="https://github.com/guest881/min_linkLists",
    author="guest881",  # 你的名字
    author_email="axijwqmxqoxmqldnq@mzjgx.dpdns.org",
    license="MIT",  # 若用 MIT 协议，需确保有 LICENSE 文件
    classifiers=[     # 分类信息，帮用户筛选包（可按需增删）
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",  # Python 版本要求
    install_requires=[],      # 依赖库（若有，填如 ["requests>=2.26.0"] ）
)
