from setuptools import setup, find_packages

setup(
    name='cellnotifier',
    version='0.1.1',  # <- Increment this each time you re-upload
    description='A lightweight library to notify the user via voice when a task or cell finishes running.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Mopoco',
    author_email='your@email.com',
    url='https://github.com/yourusername/cellnotifier',
    packages=find_packages(),
    install_requires=[
        'gTTS',
        'playsound'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.6',
)
