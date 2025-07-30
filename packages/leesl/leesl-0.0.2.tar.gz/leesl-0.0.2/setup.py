#this is a setup.py file
from setuptools import setup, find_packages


VERSION = '0.0.2'
DESCRIPTION = "Python package implementing the bivariate Lee's L statistic for spatial analysis"
LONG_DESCRIPTION = "Python package implementing the bivariate Lee's L statistic for spatial analysis"

setup(
    name="leesl",
    version=VERSION,
    author="Bence Kover",
    author_email="<kover.bence@gmail.com>",
    description=DESCRIPTION,
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "tqdm",
        "joblib",
        "statsmodels",
    ],

    keywords=['spatial', 'transcriptomics', 'visium', 'xenium', 'leesl'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X"
    ]
)

