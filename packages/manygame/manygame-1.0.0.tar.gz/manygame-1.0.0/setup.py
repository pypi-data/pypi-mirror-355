import codecs
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

VERSION = '1.0.0'
DESCRIPTION = "manygame是一个有趣的4款命令行小游戏。"
LONG_DESCRIPTION = "manygame是一个有趣的命令行小游戏。"

setup(
    name="manygame",
    version=VERSION,
    author="huangfeng",
    author_email="",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    install_requires=[],
    keywords=['python','manygame','windows','mac','linux'],
    classifiers=[
    "Development Status :: 4 - Beta",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Operating System :: OS Independent",
    "Development Status :: 4 - Beta",
    "Topic :: Games/Entertainment",
    "Topic :: Terminals",
    "Topic :: Games/Entertainment :: Puzzle Games",
    "Topic :: Games/Entertainment :: Turn Based Strategy",
    "Intended Audience :: End Users/Desktop",
    "Environment :: Console",  
    "Operating System :: Microsoft :: Windows",
    "Environment :: Win32 (MS Windows)",
]
)