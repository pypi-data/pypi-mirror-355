from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")
# 获取项目根目录
setup(
    name="student-manager",
    version="0.1.0",
    packages=find_packages(),  # 自动寻找包
    author="lyh",
    author_email="1521847437@qq.com",
    description="A simple student manager program",
    license="MIT",
    keywords="student manager",
    long_description=long_description,
    long_description_content_type='text/markdown',  # 明确指定使用 markdown 格式的描述
    # 项目的主页,一般是github的地址
    # url="https://github.com/pythonO/study/tree/master/first/20student_manager",
    entry_points={
        'console_scripts': [
            'student-manager = student_manager.main:main'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',  # python版本要求
    install_requires=[             # 依赖库
        # "requests>=2.20.0",
    ],
)
