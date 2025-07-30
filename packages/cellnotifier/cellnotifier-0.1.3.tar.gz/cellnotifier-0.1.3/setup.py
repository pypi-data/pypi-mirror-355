from setuptools import setup, find_packages
import os

setup(
    name='cellnotifier',
    version='0.1.3',
    packages=find_packages(),
    install_requires=[],
    author='Your Name',
    author_email='your@email.com',
    description='Notify when a cell or process finishes running',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
