# following https://www.youtube.com/watch?v=tEFkHEKypLI&t=176s und https://www.youtube.com/watch?v=GIF3LaRqgXo 12:48 / 29:26

# cd -> current dir
# cd "C:\Users\Creed\OneDrive\Schul-Dokumente\Programmieren\Python\Code Sammlung\Packages\creating_exception_details"

# python setup.py sdist bdist_wheel

# install current package but not in site-packages -> link to this
# pip install -e .

# pip install exception_details

# twine upload dist/*
# twine upload --skip-existing dist/*
# twine upload --verbose --skip-existing dist/*
# twine upload --verbose dist/*

from setuptools import setup, find_packages
import versioneer
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

DESCRIPTION = "Get nicely formated exception details"

# Setting up
setup(
    name="exception_details",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="André Herber",
    author_email="andre.herber.programming@gmail.com",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    install_requires=["colorful_terminal"],
    keywords=["python"],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
)
