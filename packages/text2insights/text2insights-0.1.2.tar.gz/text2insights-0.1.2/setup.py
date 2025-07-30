from setuptools import setup, find_packages
import pathlib

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name='text2insights',
    version='0.1.2',
    description='Extract sentiment, keywords, and entities from text.',
    long_description=README,
    long_description_content_type='text/markdown',
    author='Lereko Qholosha',
    packages=find_packages(),
    install_requires=[
        'textblob',
        'spacy',
        'scikit-learn',
        'numpy'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
