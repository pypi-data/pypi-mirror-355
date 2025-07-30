from setuptools import setup, find_packages

setup(
    name='pycastx',
    version='0.1.1',
    description='Elliptic Curve Cryptography and Genetic AES S-Box Optimizer',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Ahwar Khan',
    author_email='khanahwar4@gmail.com',
    url='https://github.com/ahwarkhan/pycast',
    packages=find_packages(),
    install_requires=[
        'numpy',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.7',
)
