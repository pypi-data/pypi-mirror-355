from setuptools import setup, find_packages
from os import path

# 获取当前目录路径
here = path.abspath(path.dirname(__file__))

# 读取 README 文件内容，作为 long_description
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="OERPredict",  # 库的名称
    version="1.0",  # 库的版本
    packages=find_packages(where='OERPredict', exclude=["tests"]),  # 查找 OERPredict 目录下的包
    install_requires=[  # 必需的依赖项
        'numpy>=1.18.0',
        'pandas>=1.0.0',
        'scikit-learn>=0.22.0',
        'matplotlib>=3.0.0',
        'tensorflow>=2.0.0',  # 如果使用深度学习模型，可以包含
    ],
    extras_require={  # 可选依赖，便于开发、测试和文档生成
        'dev': [  # 开发环境所需工具
            'pytest>=5.0',  # 测试框架
            'black',  # 代码格式化工具
            'flake8',  # 代码风格检查工具
            'tox',  # 用于自动化测试的工具
        ],
        'docs': [  # 文档生成所需工具
            'sphinx',  # 文档生成工具
            'sphinx_rtd_theme',  # ReadTheDocs 主题
            'numpydoc',  # 支持 Numpy 风格的文档
        ],
    },
    description="A machine learning library for predicting OER catalysis performance",  # 库的简短描述
    long_description=long_description,  # 从 README.md 读取详细描述
    long_description_content_type='text/markdown',  # 说明 README 格式为 Markdown
    author="liyihang",  # 作者信息
    author_email="liyihang@shu.edu.cn",  # 作者电子邮件
    url="https://github.com/liyihang1024/OERPredict",  # GitHub 仓库链接
    classifiers=[  # 分类信息，便于 PyPI 和其他工具识别
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
    project_urls={  # 可选，提供更多的项目相关链接
        'Documentation': 'https://yourprojectdocs.com',  # 项目文档链接
        'Source': 'https://github.com/liyihang1024/OERPredict',  # 项目源代码链接
        'Tracker': 'https://github.com/liyihang1024/OERPredict/issues',  # 项目问题追踪链接
        'Homepage': 'https://github.com/liyihang1024/OERPredict',  # 指向 GitHub 仓库首页
    },
    include_package_data=True,  # 包括 MANIFEST.in 文件中指定的文件
    package_data={  # 如果需要包括特定文件（例如数据文件），可以在这里列出
        'OERPredict': ['data/*', 'data/dataset.csv'],  # 明确列出数据文件
    },
    entry_points={  # 如果你的库包含命令行工具，可以设置命令入口
        'console_scripts': [
            'oer-predict=OERPredict.cli:main',  # 假设你有一个 cli.py 文件，入口函数为 main
        ],
    },
    # 如果需要配置命令行工具支持等，可以进一步扩展此部分
    test_suite='pytest',  # 配置测试工具，便于开发时运行测试
    tests_require=['pytest'],  # 确保安装时也安装 pytest（可选）
    # 通过 setuptools_scm 自动化版本控制，保持版本的一致性（如果你使用版本控制）
    use_scm_version=True,  # 启用版本控制管理
    setup_requires=['setuptools_scm'],  # 确保安装 setuptools_scm
    # 设置开发和生产环境兼容性
    platforms="any",  # 支持的操作系统平台
    keywords='OER, machine learning, catalysis, prediction',  # 项目的关键词
)
