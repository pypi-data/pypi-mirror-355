from setuptools import setup, find_packages
import os

version_ns = {}
with open(os.path.join("lib_ml", "version.py")) as f:
    exec(f.read(), version_ns)

setup(
    name="remla25-team7-lib-ml",
    version=version_ns["__version__"],
    packages=find_packages(),
    install_requires=[
        "nltk",
        "scikit-learn",
        "pandas"
    ],
    python_requires=">=3.8",
)
