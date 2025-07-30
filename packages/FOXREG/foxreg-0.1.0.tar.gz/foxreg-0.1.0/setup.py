from setuptools import setup, find_packages

setup(
    name='FOXREG',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
        'scipy',
        'scikit-learn',
        'matplotlib',
        'seaborn'
    ],
    author='Moses Apostol',
    author_email='mapostol@unmc.edu',
    description='A toolkit for regulatory comparison using AUCell and RSS',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Howard-Fox-Lab/FOX-Functional-OMIC-eXploration',  # optional GitHub repo
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.7',
)
