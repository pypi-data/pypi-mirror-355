from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="puppet-ai",
    version="0.1.0",
    author="PlazmaDevelopment",
    author_email="your.email@example.com",
    description="A Python module for creating and managing AI models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/puppet-ai",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires='>=3.7',
    install_requires=[
        # List your project's dependencies here
        # 'numpy>=1.19.0',
        # 'torch>=1.7.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'black',
            'isort',
            'mypy',
            'pylint',
        ],
    },
)
