from setuptools import setup, find_packages

setup(
    name="selo",         # 包名，上传 PyPI 后的名字
    version="1.4.2",                  # 版本号
    description="A simple Selenium wrapper",  # 简要描述
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="MaYunFeng",
    author_email="you@example.com",
    license="MIT",
    packages=find_packages(),         # 自动包含你的 package
    install_requires=[
        "selenium>=4.33.0",
        "attrs>=25.3.0",
        "blinker>=1.9.0",
        "certifi>=2025.4.26",
        "cffi>=1.17.1",
        "charset-normalizer>=3.4.2",
        "click>=8.2.1",
        "colorama>=0.4.6",
        "h11>=0.16.0",
        "idna>=3.10",
        "itsdangerous>=2.2.0",
        "Jinja2>=3.1.6",
        "MarkupSafe>=3.0.2",
        "MouseInfo>=0.1.3",
        "outcome>=1.3.0.post0",
        "PyAutoGUI>=0.9.54",
        "pycparser>=2.22",
        "PyGetWindow>=0.0.9",
        "PyMsgBox>=1.0.9",
        "pyperclip>=1.9.0",
        "PyRect>=0.2.0",
        "PyScreeze>=1.0.1",
        "PySocks>=1.7.1",
        "pytweening>=1.2.0",
        "PyYAML>=6.0.2",
        "requests>=2.32.4",
        "setuptools>=80.9.0",
        "sniffio>=1.3.1",
        "sortedcontainers>=2.4.0",
        "trio>=0.30.0",
        "trio-websocket>=0.12.2",
        "typing_extensions>=4.13.2",
        "urllib3>=2.4.0",
        "websocket-client>=1.8.0",
        "Werkzeug>=3.1.3",
        "wsproto>=1.2.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.13",
)
