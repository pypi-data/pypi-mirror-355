from setuptools import setup, find_packages

setup(
    name='pythonpine',
    version='0.1.2',
    author='Kushal Garg',
    description='Pine Script-style indicator engine in Python',
    packages=find_packages(),
    install_requires=[
        'MetaTrader5',
        'numpy',
        'pandas',
        'scipy',
        'scikit-learn',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)
license="AGPL-3.0",
