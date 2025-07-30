# setup.py

from setuptools import setup, find_packages

setup(
    name='zombiecipheer',
    version='1.0.0',
    author='adam',
    description='Simple XOR-based encryption library called ZombieCipher',
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
