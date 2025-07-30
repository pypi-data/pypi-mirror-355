from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mobile-terminal",
    version="0.2.0",
    author="Josharsh",
    author_email="josharsh@example.com",  # Update this with your real email
    description="The terminal moves with you - Access your terminal from any mobile device",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/josharsh/term-cast",
    py_modules=["term_cast"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Terminals",
        "Topic :: System :: Monitoring",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.7",
    install_requires=[
        "aiohttp>=3.8.0",
        "aiofiles>=0.8.0",
    ],
    entry_points={
        "console_scripts": [
            "mobile-terminal=term_cast:main_cli",
            "mterm=term_cast:main_cli",  # Short alias
        ],
    },
    keywords="terminal, broadcast, remote, mobile, websocket, cli, devtools",
    project_urls={
        "Bug Reports": "https://github.com/josharsh/term-cast/issues",
        "Source": "https://github.com/josharsh/term-cast",
    },
)