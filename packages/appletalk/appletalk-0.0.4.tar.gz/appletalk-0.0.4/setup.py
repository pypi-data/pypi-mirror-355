from setuptools import setup, find_packages

setup(
    name="appletalk",
    version="0.0.4",
    author="Annes",
    description="a Python library for macOS AppleScript dialogs and notifications",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
