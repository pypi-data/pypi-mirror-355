from setuptools import setup, find_packages

setup(
    name='eshwar-pandas',
    version='0.1.0',
    description='A lightweight wrapper around pandas for loading and previewing CSVs',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Sree Ardhanareeswaran R',
    author_email='your@email.com',
    url='https://github.com/Eshwarrsa/Eshwar_Pandas',
    packages=find_packages(),
    install_requires=[
        'pandas>=1.0.0'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.6',
)
