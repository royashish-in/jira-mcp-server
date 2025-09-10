from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="jira-mcp-standalone",
    version="1.0.0",
    author="Ashish Roy",
    author_email="royashish@example.com",
    description="JIRA MCP Server for AI assistant integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/royashish/jira-mcp-server-standalone",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
        "Topic :: Office/Business :: Groupware",
    ],
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "jira-mcp-server=server:main",
        ],
    },
    keywords="mcp jira ai model-context-protocol atlassian",
    project_urls={
        "Bug Reports": "https://github.com/royashish/jira-mcp-server-standalone/issues",
        "Source": "https://github.com/royashish/jira-mcp-server-standalone",
        "Documentation": "https://github.com/royashish/jira-mcp-server-standalone#readme",
    },
)