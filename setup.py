import os
from setuptools import setup, find_packages


directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

extras_require = {
    'embedding': ['sentence-transformers>=2.2'],
    'morphology': ['textdescriptives>=2.7', 'spacy-udpipe>=1.0'],
    'clustering': ['tslearn>=0.6', 'scipy>=1.10'],
    'viz-projection': ['umap-learn>=0.5'],
    'test': ['pytest>=6.2.2', 'hypothesis>=6.87.0'],
}
extras_require['all'] = sorted({dep for deps in extras_require.values() for dep in deps})

setup(
    name='infodynamics',
    version='0.0.1',
    packages=find_packages(),
    url='https://github.com/jankounchained/infodynamics/',
    license='CC-BY',
    author='Jan K',
    description='Ahoj',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'numpy>=1.19.0',
        'matplotlib>=3.3.2',
        'scikit-learn>=1.3.0',
        'syntok>=1.4.4',
        'typing-extensions>=4.8.0',
    ],
    extras_require=extras_require,
)