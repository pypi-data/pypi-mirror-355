import codecs
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

VERSION = '1.0.0'
DESCRIPTION = "jscx是一个结账软件。你可以使用它结账"
LONG_DESCRIPTION = "jscx是一个结账软件。你可以使用它结账。帮助收银员快速处理商品结账。"

setup(
    name="jscx",
    version=VERSION,
    author="huangfeng",
    author_email="",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    install_requires=[],
    keywords=['python','menu','jscx','windows','mac','linux'],
    classifiers=[
    "Development Status :: 4 - Beta",
    "Intended Audience :: End Users/Desktop",
    "Topic :: Office/Business :: Financial :: Accounting",
    "Topic :: Office/Business :: Financial :: Point-Of-Sale",
    "Programming Language :: Python :: 3.11",
    "Operating System :: Microsoft :: Windows",
    "Environment :: Win32 (MS Windows)",
]
)