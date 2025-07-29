from setuptools import setup, find_packages

with open("README.md", "r") as f:
    page_description = f.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="ytchanneldata",
    version="0.0.1",
    author="aveLucas",
    author_email="socialucas06@gmail.com",
    description="Search youtube channel data and store it",
    long_description=page_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aveLucas/yt-data-colector",
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.8',
)