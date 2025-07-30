from setuptools import setup, find_packages

setup(
    name='text2insights',
    version='0.1.0',
    description='Extract sentiment, keywords, and entities from text.',
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
