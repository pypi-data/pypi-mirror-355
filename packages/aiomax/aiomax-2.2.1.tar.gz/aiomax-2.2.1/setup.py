from setuptools import setup, find_packages

def readme():
    try:
        with open('pypi-description.md', encoding='utf-8') as f:
            return f.read()
    except:
        return 'Asynchronous framework for Max Bot API '

setup(
    name='aiomax',
    version='2.2.1',
    description='Asynchronous framework for Max Bot API ',
    author='oaa dpnspn',
    author_email='mbutsk@icloud.com',
    packages=find_packages(),
    install_requires=['aiohttp'],
    zip_safe=False,
    url = "https://github.com/dpnspn/aiomax",
    license="MIT License, see LICENSE.md file",
    long_description=readme(),
    long_description_content_type='text/markdown',
    project_urls={
        "GitBook docs": "https://dpnspn.gitbook.io/aiomax"
    },
    keywords = [
        "bot",
        "api",
        "asyncio",
        "max"
    ],
    classifiers = [
        "License :: OSI Approved :: MIT License",
        "Framework :: AsyncIO",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
    ]
)