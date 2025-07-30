from setuptools import setup, find_packages

with open("./README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ezwmails",
    version="1.0.1",
    packages=find_packages(),
    install_requires=[],
    author="alan1x",
    description="Ready to go implementation for sending emails with python, a simple wrapper for stmp",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alan1x/ezwmails.git",
)
