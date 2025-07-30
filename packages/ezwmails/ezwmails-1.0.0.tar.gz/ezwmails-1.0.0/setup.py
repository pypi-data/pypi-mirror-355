from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ezwmails",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[],
    author="alan1x",
    description=long_description,
    long_description_content_type="text/markdown",
)
