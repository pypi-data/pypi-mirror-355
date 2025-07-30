from setuptools import setup, find_packages

VERSION = '0.0.9'
DESCRIPTION = 'Python package for gene set enrichment in spatial transcriptomic data'
LONG_DESCRIPTION = 'Python package for gene set enrichment in spatial transcriptomic data, for more information see github.com/BKover99/spatialAUC'

setup(
    name="spatialAUC",
    version=VERSION,
    author="Bence Kover",
    author_email="kover.bence@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/plain', 
    packages=find_packages(),
    install_requires=[
        'gseapy',
        'scanpy',
        'squidpy',
        'numba',
        'tqdm'
    ],
    keywords=['spatial', 'transcriptomics', 'gsea', 'moransi', 'enrichment'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X"
    ]
)

