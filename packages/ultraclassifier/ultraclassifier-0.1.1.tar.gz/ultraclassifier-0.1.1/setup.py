from setuptools import setup, find_packages

setup(
    name="ultraclassifier",  # PyPI 上的包名（必须唯一）
    py_modules=["ultraclassifier"],  # 模块名
    version="0.1.1",  # 版本号
    author="weki",
    # 限定Python 3.8,3.9,3.10
    python_requires=">=3.8",
    install_requires=[
        "torch>=2.6.0",  # 限定torch 2.6系列
        "numpy>=2.1.0",  # 限定numpy 2.1系列
        "timm",  # timm库用于加载预训练模型
    ],
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={
        'console_scripts': [
            'ultraclassifier=ultraclassifier.python_api:main'
        ]
    },
)