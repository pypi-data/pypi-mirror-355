import os
import re
import sys

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
with open("optimihost/constants.py") as fh:
    VERSION = re.search('__version__ = \'([^\']+)\'', fh.read()).group(1)

# 'setup.py publish' shortcut.
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist bdist_wheel')
    os.system('twine upload dist/*')
    sys.exit()


setuptools.setup(
    name="optimihost",
    version=VERSION,
    author="OptimiHost and EAMCVD",
    author_email="info@optimihost.com",
    description="API For optimihost",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/iamkubi/pydactyl",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.4',
    install_requires=[
        "requests >=2.21.0",
    ],
    tests_require=[
        "pytest >=3",
        "pytest-cov",
    ],
    project_urls={
        "Website": "https://developer.optimihost.com/",
        "Source": "https://github.com/iamkubi/pydactyl",
    }
)
