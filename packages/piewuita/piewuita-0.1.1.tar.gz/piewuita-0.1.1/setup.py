# setup.py

from setuptools import setup, find_packages

setup(
    name='piewuita',
    version='0.1.1',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'piewuita': ['templates/.gitignore'],
    },
    install_requires=[
        
    ],
    author='Juan Díaz',
    author_email='juandiazfdez1992@gmail.com',
    description='Init project python',
    long_description=open('readme.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Fuan200/',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': [
            'piewuita=scripts.piewuita_cli:main', 
        ],
    },
)
