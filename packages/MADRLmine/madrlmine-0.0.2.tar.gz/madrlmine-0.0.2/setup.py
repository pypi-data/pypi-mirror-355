import os
import setuptools
from setuptools import setup, find_packages

# 允许setup.py在任何路径下执行
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setuptools.setup(
    name="MADRLmine",  # 库名
    version="0.0.2",  # 版本号
    author="kw-zheng",  # 作者
    author_email="kw-zheng@sjtu.edu.cn",  # 作者邮箱
    description="A small example package",  # 简介
    long_description="long_description",  # 详细描述
    long_description_content_type="text/markdown",  # 描述语法
    url="https://github.com/kw-zheng/MADRLMine_pip",  # 项目主页
    packages=find_packages(),
    package_data={
        "MADRLmine": [
            "MADRLmine/data/*.npy",
            "MADRLmine/VehicleModel_dll/*.so",
            "MADRLmine/VehicleModel_dll/*.dll"
        ]
    },
    include_package_data=True,  # 激活 MANIFEST.in 文件
    classifiers=[  # 指定库的分类器
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[  # 依赖库
        'pyautogui',
        'Django >= 1.11',
    ],
    python_requires='>=3.6',
)