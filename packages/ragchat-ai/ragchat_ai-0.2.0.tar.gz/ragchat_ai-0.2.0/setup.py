from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ragchat-ai",
    version="0.2.0",
    packages=find_packages(include=["ragchat"]),
    install_requires=[
        "litellm~=1.68.2",
        "asyncpg~=0.30.0",
        "neo4j~=5.28.1",
        "pydantic-settings~=2.8.1",
        "cachetools~=5.5.2",
        "rapidfuzz~=3.12.2",
        "aiofiles~=24.1.0",
        "base58~=2.1.1",
        "qdrant-client~=1.14.2",
        "scikit-learn~=1.7.0",
        "fastembed~=0.7.0",
    ],
    extras_require={
        "dev": [
            "pytest-asyncio",
            "ruff",
            "mypy",
            "types-cachetools",
            "types-aiofiles",
            "asyncpg-stubs",
        ]
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Raul Ricardo Sanchez",
    author_email="ricardo3820@gmail.com",
    description="RagChat transforms unstructured data for LLM interaction.",
    url="https://github.com/raul3820/ragchat",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    license="MIT",
    include_package_data=True,
    package_data={
        "ragchat": ["py.typed", "*.pyi"],
    },
)
