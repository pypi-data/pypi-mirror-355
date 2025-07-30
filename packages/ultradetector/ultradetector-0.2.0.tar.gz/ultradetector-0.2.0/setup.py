from setuptools import setup, find_packages

setup(
    name="ultradetector",  # PyPI library
    py_modules=["ultradetector"],  # module name
    version="0.2.0",  # version
    author="weki",
    # Python version
    python_requires=">=3.8",
    install_requires=[
        "numpy",
        "nibabel",
        "matplotlib",
        "opencv-python",
        "psutil",
        "pyyaml",
        "requests",
        "ultralytics"
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
