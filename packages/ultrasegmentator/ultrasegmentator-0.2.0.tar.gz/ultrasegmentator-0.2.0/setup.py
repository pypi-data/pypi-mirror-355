from setuptools import setup, find_packages

setup(
    name="ultrasegmentator",  # PyPI library
    py_modules=["ultrasegmentator"],  # module name
    version="0.2.0",  # version
    author="weki",
    # Python version
    python_requires=">=3.8",
    install_requires=[
        "torch",
        "numpy",
        "tqdm",
        "acvl-utils",
        "batchgenerators",
        "nibabel",
        "dynamic_network_architectures",
        "batchgeneratorsv2",
        "matplotlib",
        "seaborn",
        "blosc2"
    ],
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={
        'console_scripts': [
            'ultrasegmentator=ultrasegmentator.python_api:main'
        ]
    },
)
