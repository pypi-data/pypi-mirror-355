# setup.py
from setuptools import setup, find_packages

setup(
    name="OERPredict",  # 库的名称
    version="0.1",  # 库的版本
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
        'scikit-learn',
        'matplotlib'
    ],
    description="A machine learning library for predicting OER catalysis performance",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/OERPredict",  # GitHub 仓库链接
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
