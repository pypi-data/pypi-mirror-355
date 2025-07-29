from setuptools import find_packages, setup

from huscy_project import __version__


setup(
    name='huscy-project',
    version=__version__,

    description='integration project for huscy apps',

    author='Stefan Bunde',
    author_email='stefanbunde+git@posteo.de',

    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'huscy=huscy_project.bin.huscy:main',
        ],
    },
    install_requires=[
        'Django>=4.2',
    ],
    extras_require={
        'testing': ['tox'],
    },
)
