from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="actvalue.lambda-mcp-server",
    version="1.0.0",
    author="ActValue",
    description="A Lambda-based MCP (Model Context Protocol) server implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/lambda-mcp-server",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.12",
    install_requires=[
        "redis>=6.0.0",
        "actvalue.aws-pysdk>=0.3.0",
    ],
    extras_require={
        "dev": [
            "boto3>=1.36.0",
            "fastapi>=0.115.12",
            "uvicorn>=0.34.2",
        ],
    },
)
