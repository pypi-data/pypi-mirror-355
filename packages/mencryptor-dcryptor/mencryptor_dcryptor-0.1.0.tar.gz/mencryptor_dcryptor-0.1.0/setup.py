from setuptools import setup, find_packages

setup(
    name='mencryptor-dcryptor',
    version='0.1.0',
    packages=find_packages(),
    author='manik121',
    author_email='yhmanik789@gmail.com',
    description='Custom Python code encryptor and decryptor using defined character mappings. Made by Yeahya Hamza',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/#/mencryptor-dcryptor',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
