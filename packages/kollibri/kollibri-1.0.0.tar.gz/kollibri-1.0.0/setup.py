import os

from setuptools import setup


def read(fname):
    """
    Helper to read README
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read().strip()


setup(
    name="kollibri",
    version="1.0.0",
    description="Extract collocations from VERT data",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    url="https://gitlab.uzh.ch/corpus-linguistic-uzh/kollibri",
    author="Danny McDonald, Sonja Huber",
    include_package_data=False,
    zip_safe=True,
    packages=["kollibri"],
    scripts=["bin/kollibri"],
    author_email="noah.bubenhofer@ds.uzh.ch",
    license="MIT",
    keywords=["corpus", "linguistics", "corpora", "collocation", "vert"],
    install_requires=["tqdm"],
)
