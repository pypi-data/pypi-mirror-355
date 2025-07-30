# setup.py

from setuptools import setup, find_packages
# "name" needs to be lowercase

setup(
    name='thetakde',
    version='0.1.1',
    author='DSML-book',
    author_email='kroese@maths.uq.edu.au',
    description='A package for the theta kernel density estimator',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/DSML-book/ThetaKDE',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'scipy',
        'matplotlib',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
