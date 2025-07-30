from setuptools import setup, find_packages
from io import open


def read(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()


setup(
    name="HeleketAPI",
    version="0.0.1.dev",
    description="Easy interaction with Heleket API, support for asynchronous approaches",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Fsoky",
    url="https://github.com/Fsoky/CryptomusAPI",
    author_email="cyberuest0x12@gmail.com",
    keywords="api heleket asyncio crypto heleketapi",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages()
)
