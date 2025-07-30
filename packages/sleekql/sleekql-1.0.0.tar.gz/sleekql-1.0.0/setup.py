from setuptools import setup, find_packages
import os

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="sleekql",
    version="1.0.0",
    description="A light SQLite3 wrapper for easier database operations in Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="jstiin",
    url="https://github.com/jstiin/sleekql",
    packages=find_packages(),
    install_requires=[],
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Topic :: Database :: Database Engines/Servers",
    ],
    keywords="sqlite sqlite3 database wrapper orm sleekql",
    license="AGPL-3.0-only",
    include_package_data=True,
)
