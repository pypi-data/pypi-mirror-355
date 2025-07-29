from setuptools import setup, find_packages

"""
:authors: @litemat
:license: The MIT License (MIT), see LICENSE file
:copyright: (c) 2025 @litemat  
"""

version = '0.2'

with open('README.md', encoding='utf-8') as file:
    read_me_description = file.read()

setup(
    name='altel_b2b_api',
    version=version,

    author='@litemat',
    author_email='legentea22@gmail.com',

    description='Библиотека предоставляет удобный интерфейс для взаимодействия с Altel B2B API',
    long_description=read_me_description,
    long_description_content_type= 'text/markdown',

    url='https://github.com/litemat/altel_api',
    download_url='https://github.com/litemat/altel_api/archive/v{}.zip'.format(
        version
    ),

    license='The MIT License (MIT), see LICENSE file',

    packages=find_packages(),
    install_requires=[
        "setuptools>=80.9.0",
        "dotenv>=0.9.9",
        "python-dotenv>=1.1.0",
        "cloudscraper>=1.2.71"
    ],

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

)
