import setuptools
from emr_analysis import __version__, __author__, __author_email__

with open('requirements.txt') as f:
    requirements = []
    for library in f.read().splitlines():
        requirements.append(library)

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name = 'emr-analysis',
    version = __version__,
    author = __author__,
    author_email = __author_email__,
    license = 'The MIT License (MIT)',
    description = 'A simple analysis and visualisation package for simulated EMR data.',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/AnkitArni/simulated-emr-analysis',
    packages = setuptools.find_packages(),
    include_package_data = True,
    classifiers = [
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires = '>=3.8.0',
    install_requires = requirements,
)
