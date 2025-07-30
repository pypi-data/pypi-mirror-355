from setuptools import setup, find_packages

setup(
    name="ultrasegmentator",  # PyPI 上的包名（必须唯一）
    py_modules=["ultrasegmentator"],  # 模块名
    version="0.1.2",  # 版本号
    author="weki",
    # 限定Python 3.8,3.9,3.10
    python_requires=">=3.8, <3.11",
    install_requires=[
        "torch>=2.6",  # 限定torch 2.6系列
        "numpy>=2.1",  # 限定numpy 2.1系列
        "tqdm",
        "acvl_utils",
        "batchgenerators",
        "nibabel",
        "dynamic_network_architectures",
        "batchgeneratorsv2",
        "matplotlib",
        "seaborn"
    ],
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
    ]
)