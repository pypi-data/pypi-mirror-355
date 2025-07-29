from setuptools import setup, find_packages
import sys

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define dependencies based on Python version
if sys.version_info >= (3, 7) and sys.version_info < (3, 8):
    REQUIRES = ["requests>=2.25.0", "urllib3>=1.26.0"]
else:
    REQUIRES = ["requests>=2.25.0", "urllib3>=1.26.0"]

setup(
    name="loglito",
    version="0.0.1",
    author="Loglito Team",
    author_email="support@loglito.io",
    description="Python client library for Loglito logging service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://loglito.io",
    project_urls={
        "Homepage": "https://loglito.io",
        "Documentation": "https://loglito.io/docs",
        "Repository": "https://github.com/loglito/loglito-python",
        "Issues": "https://github.com/loglito/loglito-python/issues",
    },
    packages=find_packages(),
    install_requires=REQUIRES,
    python_requires=">=3.7",
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
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
    ],
    keywords=["logging", "loglito", "observability", "monitoring"],
    license="MIT",
)
