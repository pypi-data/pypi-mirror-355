from setuptools import setup, find_packages

setup(
    name="ultradetector",  # PyPI 上的包名（必须唯一）
    py_modules=["ultradetector"],  # 模块名
    version="0.1.15",  # 版本号
    author="weki",
    # 限定Python 3.8,3.9,3.10
    python_requires=">=3.8",
    install_requires=[
        "numpy",
        "nibabel",
        "matplotlib",
        "opencv-python",
        "psutil",
        "pyyaml",
        "requests"
    ],
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={
        'console_scripts': [
            'ultradetector=ultradetector.python_api:main'
        ]
    },
)
