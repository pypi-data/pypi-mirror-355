"""
Setup configuration for the streaming XML parser package.
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
def read_file(filename):
    """Read a file and return its contents."""
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, filename), encoding='utf-8') as f:
        return f.read()

# Package metadata
NAME = "streaming-xml-parser"
VERSION = "1.0.0"
DESCRIPTION = "High-performance streaming XML parser for real-time applications"
LONG_DESCRIPTION = read_file("README.md")
AUTHOR = "Agnostech"
EMAIL = "ravi@agnostech.ca"
URL = "https://github.com/AgnostechAI/xmlstream"

# Requirements
REQUIRED = [
    # No external dependencies for core functionality
]

EXTRAS = {
    'dev': [
        'pytest>=6.0.0',
        'pytest-cov>=2.0.0',
        'black>=21.0.0',
        'flake8>=3.8.0',
        'mypy>=0.800',
    ],
    'docs': [
        'sphinx>=3.0.0',
        'sphinx-rtd-theme>=0.5.0',
    ]
}

# All extras
EXTRAS['all'] = sum(EXTRAS.values(), [])

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    packages=find_packages(exclude=['tests', 'tests.*', 'examples', 'examples.*']),
    python_requires='>=3.8',
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Markup :: XML',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    keywords='xml parser streaming real-time performance',
    project_urls={
        'Bug Reports': f'{URL}/issues',
        'Source': URL,
        'Documentation': f'{URL}/docs',
    },
    zip_safe=False,
    include_package_data=True,
) 