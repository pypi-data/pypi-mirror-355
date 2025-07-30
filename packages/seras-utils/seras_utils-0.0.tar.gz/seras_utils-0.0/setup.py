from setuptools import setup, find_packages

with open('README.md', 'r') as file:
    long_description = file.read()

setup(
    name='seras_utils',
    version='0.0',
    packages=find_packages(),
    install_requires=[
        'openai',
    ],
)