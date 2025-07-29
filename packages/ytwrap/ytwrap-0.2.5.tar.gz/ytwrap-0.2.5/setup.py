from setuptools import setup, find_packages

with open("pypi.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="ytwrap",
    version="0.2.5",
    description="Python wrapper for the YouTube Data API v3.",
    author="Himarry",
    url="https://github.com/Himarry/ytwrap",
    project_urls={
        "Source": "https://github.com/Himarry/ytwrap",
        "Tracker": "https://github.com/Himarry/ytwrap/issues",
    },
    packages=find_packages(),
    install_requires=[
        "google-api-python-client",
        "isodate",
        "pytz"
    ],
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
)
