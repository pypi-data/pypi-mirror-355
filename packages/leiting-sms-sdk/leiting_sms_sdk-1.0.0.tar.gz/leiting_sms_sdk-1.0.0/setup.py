#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# 读取版本信息
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), "leiting_sms_sdk.py")
    with open(version_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "1.0.0"

setup(
    name="leiting-sms-sdk",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="雷霆短信验证码服务 Python SDK",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/leiting-sms-sdk",
    py_modules=["leiting_sms_sdk"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    keywords="sms, verification, code, leiting, 短信, 验证码, 雷霆",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/leiting-sms-sdk/issues",
        "Source": "https://github.com/yourusername/leiting-sms-sdk",
        "Documentation": "https://github.com/yourusername/leiting-sms-sdk#readme",
    },
)
