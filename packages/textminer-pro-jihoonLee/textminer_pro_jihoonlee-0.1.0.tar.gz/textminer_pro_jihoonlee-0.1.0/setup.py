from setuptools import setup, find_packages

setup(
    name='textminer-pro-jihoonLee',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'nltk',
        'scikit-learn',
        'sumy',
        'langdetect'
    ],
    author='Jihoon Lee',
    author_email='dlwlgns7540@naver.com',
    description='A simple text mining package with stopword removal, keyword extraction, summarization, and language detection.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/hoonZeee/Oss_2025/tree/main/pypi',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.7',
)
