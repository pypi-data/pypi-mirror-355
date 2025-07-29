# -*- coding: utf-8 -*-
"""
Created on 2025/6/13 22:50
@author: guest881
"""
from setuptools import setup, find_packages
#Xz.1qaz@WSX
#令牌 pypi-AgEIcHlwaS5vcmcCJGFjMmVkNzY3LWY1MDgtNDVjYi05NmJjLWMyNTAyYTU3ZDFhOAACKlszLCI4ZDgxNmY1Zi0xMDk4LTRkNDYtOTNiNC1jZGI2OGNiYWYyYjAiXQAABiAPJ_uESiKxzOzZbtEsUHPOCKKLB_W5tIoxENlD4LrTlA
setup(
    name="guest881-linkLists",  # 包名，PyPI 上唯一，若已存在需换名（可去 PyPI 搜搜看）
    version="0.2.1",   # 版本号，遵循语义化（如 主版本.次版本.补丁）
    packages=find_packages(),  # 自动发现包（会包含 linkLists 目录）
    description="最基础的链表库，自娱自乐，目前仅支持环形链表、常规链表，新增了去重链表，修复了一些越界行为和BUG",
    url="https://github.com/guest881/min_linkLists",
    author="guest881",  # 你的名字
    author_email="axijwqmxqoxmqldnq@mzjgx.dpdns.org",
    license="MIT",  # 若用 MIT 协议，需确保有 LICENSE 文件
    classifiers=[     # 分类信息，帮用户筛选包（可按需增删）
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",  # Python 版本要求
    install_requires=[],      # 依赖库（若有，填如 ["requests>=2.26.0"] ）
)
