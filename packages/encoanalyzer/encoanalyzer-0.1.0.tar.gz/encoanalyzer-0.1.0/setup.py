from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='encoanalyzer',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'matplotlib',
        'numpy',
        'colorama',
    ],
    entry_points={
        'console_scripts': [
            'encoanalyzer=encoanalyzer.core:main',
        ],
    },
    author='Adam Alcander',
    description='A tool for encoding and analyzing text bytes visually',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
)
