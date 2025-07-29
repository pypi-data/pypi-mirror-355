from setuptools import setup, find_packages
import os

# 读取README文件
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="runtime-provisioner",
    version="1.0.0",
    author="Runtime Provisioner Team", 
    author_email="contact@example.com",
    description="运行时依赖自动下载器 - 自动下载和管理运行时依赖",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/runtime-provisioner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8", 
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Installation/Setup",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    install_requires=[
        "wget>=3.2",
    ],
    keywords="download, dependencies, runtime, provisioner, automation",
    project_urls={
        "Bug Reports": "https://github.com/your-username/runtime-provisioner/issues",
        "Source": "https://github.com/your-username/runtime-provisioner",
    },
) 