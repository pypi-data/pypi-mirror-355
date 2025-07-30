from setuptools import setup, find_packages
from os import path

# 获取当前目录路径
here = path.abspath(path.dirname(__file__))

# 读取 README 文件内容，作为 long_description
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="OERPredict",  # 库的名称
    version="0.7",  # 库的版本
    packages=find_packages(where='OERPredict', exclude=["tests"]),  # 查找 OERPredict 目录下的包
    install_requires=[
        'numpy>=1.18.0',  # 指定最低版本
        'pandas>=1.0.0',
        'scikit-learn>=0.22.0',
        'matplotlib>=3.0.0',
    ],
    extras_require={  # 可选依赖，方便开发或测试
        'dev': [
            'pytest>=5.0',
            'black',  # 代码格式化工具
            'flake8',  # 代码检查工具
        ],
        'docs': [
            'sphinx',  # 文档生成工具
            'sphinx_rtd_theme',  # 主题
        ],
    },
    description="A machine learning library for predicting OER catalysis performance",
    long_description=long_description,  # 从 README.md 读取详细描述
    long_description_content_type='text/markdown',  # 指定 README 格式
    author="liyihang",
    author_email="liyihang@shu.edu.cn",
    url="https://github.com/liyihang1024/OERPredict",  # GitHub 仓库链接
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    python_requires='>=3.6',  # 支持的 Python 版本
    project_urls={  # 可选，添加更多关于项目的链接
        'Documentation': 'https://yourprojectdocs.com',
        'Source': 'https://github.com/liyihang1024/OERPredict',
        'Tracker': 'https://github.com/liyihang1024/OERPredict/issues',
    },
    include_package_data=True,  # 包括 MANIFEST.in 文件中指定的文件
    package_data={  # 如果需要包括特定文件（例如数据文件），可以在这里列出
        'OERPredict': ['data/*', 'data/dataset.csv'],  # 明确列出数据文件
    },
    entry_points={  # 如果你的库包含命令行工具，可以设置命令入口
        'console_scripts': [
            'oer-predict=OERPredict.cli:main',  # 假设你有一个 cli.py 文件，如果没有可以忽略
        ],
    },
    # 如果需要配置命令行工具支持等，可以进一步扩展此部分
)
