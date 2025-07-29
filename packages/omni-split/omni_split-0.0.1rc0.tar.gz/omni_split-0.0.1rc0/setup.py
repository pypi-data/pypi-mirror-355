from setuptools import setup, find_packages
import os

def get_requirements():
    """Read requirements from requirements.txt and return as a list."""
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="omni_split",
    version="0.0.1c",  # 你的版本号
    author="dinobot22",
    author_email="2802701695yyb@gmail.com",
    description="A comprehensive document splitting toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dinobot22/omni_split",
    packages=find_packages(),
    package_data={
        "omni_split": ["model/text_chunker_tokenizer/qwen_tokenizer.json"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=get_requirements(),
)