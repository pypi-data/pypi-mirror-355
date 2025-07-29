from setuptools import setup, find_packages

setup(
    name='aptamerforge',
    version='0.1.7.2',
    description='A DNA aptamer screening tool for mismatch analysis and hairpin detection & drawing',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='William Asamoah',
    author_email='cephaswills@gmail.com',
    url='https://github.com/Feicheiel/aptamerforge',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'viennarna',  # if using pip version of ViennaRNA
        'pycairo>=1.20.0b'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)