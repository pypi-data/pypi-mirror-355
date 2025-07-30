from setuptools import setup, find_packages

setup(
    name="ultraclassifier",  # PyPI library
    py_modules=["ultraclassifier"],  # module name
    version="0.2.2",  # version
    author="weki",
    # Python version
    python_requires=">=3.8",
    install_requires=[
        "torch",  
        "numpy",  
        "timm", 
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