from setuptools import setup, find_packages
import os

setup(
    name='gitsnipe',
    version='1.0.1',
    packages=find_packages(),
    install_requires=[
        'requests>=2.28.0',
        'configparser>=5.3.0',
        'gitpython>=3.1.30',
        'rich>=13.0.0',
        'typer>=0.9.0',
        'git-dumper>=1.0.0'
    ],
    entry_points={
        'console_scripts': [
            'gitsnipe=gitsnipe.cli:main',
        ],
    },
    author='Ishan Oshada',
    author_email='example@example.com',
    description='A powerful tool for scanning and cloning Git repositories with exposed .git/config files',
    long_description=open('README.md', encoding='utf-8').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    url='https://github.com/ishanoshada/GitSnipe',
    license='MIT',
    keywords='git security scanning repository clone config credentials automation tool',
    project_urls={
        'Bug Reports': 'https://github.com/ishanoshada/GitSnipe/issues',
        'Source': 'https://github.com/ishanoshada/GitSnipe',
        'Documentation': 'https://github.com/ishanoshada/GitSnipe#readme',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Security',
        'Topic :: Software Development :: Version Control :: Git',
    ],
    python_requires='>=3.7',
)