from setuptools import setup, find_packages
import os


# Read version from __init__.py
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), "toothfairy_cli", "__init__.py")
    with open(version_file, "r") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    raise RuntimeError("Cannot find version string")


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="toothfairy-cli",
    version=get_version(),
    author="ToothFairy AI",
    author_email="support@toothfairyai.com",
    description="Command-line interface for ToothFairy AI API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitea.toothfairyai.com/ToothFairyAI/tooth-fairy-website/toothfairy-cli",
    project_urls={
        "Bug Reports": "https://gitea.toothfairyai.com/ToothFairyAI/tooth-fairy-website/toothfairy-cli/issues",
        "Source": "https://gitea.toothfairyai.com/ToothFairyAI/tooth-fairy-website/toothfairy-cli",
        "Documentation": "https://gitea.toothfairyai.com/ToothFairyAI/tooth-fairy-website/toothfairy-cli#readme",
        "Releases": "https://gitea.toothfairyai.com/ToothFairyAI/tooth-fairy-website/toothfairy-cli/releases",
    },
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
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "click>=8.0.0",
        "python-dotenv>=0.19.0",
        "rich>=12.0.0",
        "pyyaml>=6.0",
        "httpx>=0.24.0",
        "httpx-sse>=0.4.0",
    ],
    entry_points={
        "console_scripts": [
            "toothfairy=toothfairy_cli.cli:main",
            "tf=toothfairy_cli.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "toothfairy_cli": ["*.py"],
    },
)
