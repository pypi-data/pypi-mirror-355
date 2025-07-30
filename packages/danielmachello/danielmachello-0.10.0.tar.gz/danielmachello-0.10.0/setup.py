from setuptools import setup, find_packages

setup(
    name='danielmachello',
    version='0.10.0',
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "danielmachello = danielmachello.main:hello"
        ],
    },
)
