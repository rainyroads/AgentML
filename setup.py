"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
# from codecs import open
from os import path
# from agentml import __version__

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
# with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
#     long_description = f.read()

setup(
    name='AgentML',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.2a1',

    description='An XML dialect for creating natural language software agents',
    # long_description=long_description,

    # The project's main homepage.
    url='https://github.com/FujiMakoto/AgentML',

    # Author details
    author='Makoto Fujimoto',
    author_email='makoto@makoto.io',

    # License
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',

        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Text Processing :: Markup :: XML'
    ],

    keywords=['bot', 'chatbot', 'chatterbot', 'ai', 'aiml', 'rivescript'],

    packages=find_packages(exclude=['tests', 'demo']),
    install_requires=['lxml>=3.4.4,<3.5'],

    package_data={
        'agentml': ['intelligence/*.aml', 'schemas/*.rng', 'schemas/*.xsd', 'schemas/tags/*.rng'],
    },
)
