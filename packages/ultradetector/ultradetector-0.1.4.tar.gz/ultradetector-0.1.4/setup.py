from setuptools import setup, find_packages

setup(
    name="ultradetector",  # PyPI 上的包名（必须唯一）
    py_modules=["ultradetector"],  # 模块名
    version="0.1.4",  # 版本号
    author="weki",
    # 限定Python 3.8,3.9,3.10
    python_requires=">=3.8",
    install_requires=[
        "torch>=2.6",  # 限定torch 2.6系列
        "numpy>=2.1",  # 限定numpy 2.1系列
        "nibabel",
        "matplotlib",
        "opencv-python",
        "psutil"
    ],
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
    ]
)