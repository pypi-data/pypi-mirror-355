from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ppe-debug",
    version="1.0.1",
    author="Alex Jiakai Xu",
    author_email="jiakai.xu@columbia.edu",
    description="PrePrintExec - AST-based debugging tool that prints before execution",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Alex-XJK/PrePrintExec",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=[
        # No external dependencies needed!
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black",
            "flake8",
            "mypy",
        ],
    },
    keywords="debugging, ast, compiler, parser, python",
)