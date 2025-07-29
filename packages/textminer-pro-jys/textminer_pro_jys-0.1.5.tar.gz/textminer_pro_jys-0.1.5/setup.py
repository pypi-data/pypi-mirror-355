# setup.py (중요 부분만)

from pathlib import Path
from setuptools import setup, find_packages

this_dir = Path(__file__).parent
long_description = (this_dir / "README.md").read_text(encoding="utf-8")

setup(
    name="textminer-pro-jys",
    version="0.1.5",                             
    description="Advanced text mining utils",
    long_description=long_description,            
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "nltk>=3.8", "scikit-learn>=1.4",
        "sumy>=0.11", "langdetect>=1.0",
    ],
)