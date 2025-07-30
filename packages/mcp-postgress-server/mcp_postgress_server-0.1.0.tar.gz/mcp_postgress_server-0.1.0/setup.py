from setuptools import setup, find_packages

setup(
    name="employee-analytics-mcp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain",
        "langchain-community",
        "openai",
        "psycopg2-binary",
        "httpx",
        "python-dotenv",
    ],
    author="Nancy Madan",
    author_email="nancymadan.6@gmail.com",
    description="An MCP server that connects to a PostgreSQL database and does deep web search to answer all your questions",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/SwiftAlice/mcp_postgress_server.git",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)