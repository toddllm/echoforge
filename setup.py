"""
Setup script for EchoForge package.
"""

import os
from setuptools import setup, find_packages

# Get version from __init__.py
with open(os.path.join('app', '__init__.py'), 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip('"\'')
            break
    else:
        version = '0.1.0'

# Read requirements
with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read development requirements
with open('requirements-dev.txt', 'r') as f:
    dev_requirements = []
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('-r'):
            dev_requirements.append(line)

# Read the README for the long description
with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='echoforge',
    version=version,
    description='Character voice generation application',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='EchoForge Team',
    author_email='info@echoforge.ai',
    url='https://github.com/toddllm/echoforge',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        'dev': dev_requirements,
    },
    entry_points={
        'console_scripts': [
            'echoforge=app.main:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.9',
) 