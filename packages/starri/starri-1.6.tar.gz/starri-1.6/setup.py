from setuptools import setup, find_packages

setup(
    name='starri',
    version='1.6',
    packages=find_packages(),
    install_requires=[
        'blessed>=1.20.0',
        'py-gradify',
    ],
    description="A terminal-based menu system using blessed.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author="Rowan Barker",
    author_email="barker.rowan@sugarsalem.com",
    url="https://github.com/lioen-dev/starri",
)
