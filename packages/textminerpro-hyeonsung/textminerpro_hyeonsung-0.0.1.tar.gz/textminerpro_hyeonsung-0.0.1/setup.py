from setuptools import setup, find_packages

setup(
    name='textminerpro-hyeonsung',
    version='0.0.1',
    author='정현성',
    author_email='2254784@donga.ac.kr',
    packages=find_packages(),
    install_requires=[
        'nltk',
        'scikit-learn',
        'sumy',
        'langdetect'
    ],
    description='Advanced text preprocessing package',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/dau-J/pypi_textminor.git',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
