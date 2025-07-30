from setuptools import setup, find_packages

setup(
    name="smartsys-analyzer",
    version="1.0.0",
    author="Adam Alcander et Eden",
    author_email="aeden6877@gmail.com",
    description="Advanced system monitoring and analyzer toolkit for Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/EdenGithhub/smartsys-analyzer",  # ✅ Ganti username

    project_urls={
        "Documentation": "https://github.com/EdenGithhub/smartsys-analyzer/wiki",
        "Source": "https://github.com/EdenGithhub/smartsys-analyzer",
        "Tracker": "https://github.com/EdenGithhub/smartsys-analyzer/issues"
    },

    packages=find_packages(),
    include_package_data=True,

    install_requires=[
        "pydantic>=2.0",
        "psutil>=5.9",
        "colorama>=0.4",
        "rich>=13.0",
        "playsound>=1.3",
        "schedule",
        "tabulate",
        "matplotlib",
        "humanize",
        "pyyaml",
        "jsonschema",
        "typing-extensions",
        "platformdirs",
        "typer"
    ],

    python_requires=">=3.6",  # ✅ Disamakan dengan pyproject.toml

    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent"
    ],

    license="MIT",
    keywords="monitoring system-analyzer system-health resource-checker",
)
