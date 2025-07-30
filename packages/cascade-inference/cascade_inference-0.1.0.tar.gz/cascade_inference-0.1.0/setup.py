from setuptools import setup, find_packages

setup(
    name="cascade-inference",
    version="0.1.0",
    author="Eli Butters",
    author_email="elibutters@outlook.com",
    description="Cascade based inference for large language models.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/elibutters/cascadeinference",
    packages=find_packages(),
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "openai",
        "requests",
    ],
    extras_require={
        "test": ["pytest", "pytest-asyncio", "python-dotenv"],
        "semantic": ["fastembed", "scipy"],
    }
) 