from setuptools import setup, find_packages

setup(
    name='Pharmalyzer',
    version='0.1',
    author='[Sorour Hassani]',
    author_email='s.hassani@alum.semnan.ac.ir & sorour.hasani@gmail.com',
    description='Pharmaceutical ADME/Tox filtering and analysis toolkit',
    packages=find_packages(),
    license='MIT',
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    install_requires=[
        'rdkit',
        'fuzzywuzzy',
        'python-Levenshtein'
    ],
)