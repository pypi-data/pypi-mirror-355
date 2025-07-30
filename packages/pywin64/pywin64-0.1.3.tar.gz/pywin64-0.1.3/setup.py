from io import open
from setuptools import setup

"""
:authors: KingsFrown
:license: Apache License, Version 2.0, see LICENSE file
:copyright: (c) 2025 KingsFrown
"""

version = '0.1.3'
'''
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()
'''

long_description = '''Python module for dl ekz'''

setup(
    name='pywin64',
    version=version,

    author='KingsFrown',
    author_email='garik.karymov@yandex.ru',

    description='''dl ekz''',
    long_description=long_description,
    # long_description_content_type='text/markdown',

    url='https://github.com/KingsFrown/pywin64',
    download_url='https://github.com/KingsFrown/pywin64/archive/v{}.zip'.format(version),

    license='Apache License, Version 2.0, see LICENSE file',

    packages=['pywin64'],
    install_requires=['pyperclip'],

    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: CPython',
    ]
)