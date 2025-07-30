from setuptools import setup

setup(
    name="TLogger4",
    version="1.0",
    packages=["TLogger4"],
    description="Colored logger with console/file output",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Yrzd6",
    author_email="",
    url="https://github.com/yrzd6",
    license="MPL-2.0",
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 4 - Beta",
        "Topic :: Utilities"
    ],
    python_requires=">=3.10",
)