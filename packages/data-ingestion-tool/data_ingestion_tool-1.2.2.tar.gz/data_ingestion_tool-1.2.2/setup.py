from setuptools import setup, find_packages

setup(
    name='data_ingestion_tool',
    version='1.2.2',
    author='Bug Hunter',
    author_email='sayhi@thekingof.cool',
    description='A toolset for ingesting data from Box into Delta tables, and exporting data to Box.',
    packages=find_packages(),
    install_requires=[
        'boxsdk',
        'pandas',
        'cerberus',
        'cerberus-python-client',
        'openpyxl',
        'pyspark',
        'delta-spark'
    ],
    python_requires='>=3.6',
)