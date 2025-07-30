from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    install_requires = [line.strip() for line in fh if line.strip() and not line.startswith('#')]

setup(
    name="agentic-de",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Agentic Data Engineering tools and protocols (MCP, stdio, sse, FastAPI, etc)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MANMEET75/MCP-Agentic-Data-Engineering",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            # Add CLI entry points here if needed, e.g.:
            # "agentic-de=mcp_client.stdio.mcp_client:main",
        ]
    },
)