# setup.py
from setuptools import setup, find_packages

setup(
    name='brokeapi',
    version='1.0.1',
    description='Simple Python client for BrokeAPI chat endpoint',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='NotHerXenon',
    author_email='rifatarefinchowdhury@gmail.com',
    url='https://github.com/rifatgamingop/brokeapi',  # Optional repo URL
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
