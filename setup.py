import os
import re
from setuptools import setup, find_packages


directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


def _read_version() -> str:
    """Reads __version__ out of infodynamics/__init__.py with a regex rather
    than importing the package, so building the sdist/wheel doesn't require
    infodynamics' runtime deps to already be installed."""
    init_path = os.path.join(directory, "infodynamics", "__init__.py")
    with open(init_path, encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]+)[\'"]', content, re.M)
    if not match:
        raise RuntimeError(f"could not find __version__ in {init_path}")
    return match.group(1)

extras_require = {
    'embedding': ['sentence-transformers>=2.2'],
    'morphology': ['textdescriptives>=2.7', 'spacy-udpipe>=1.0'],
    'clustering': ['tslearn>=0.6', 'scipy>=1.10'],
    'viz-projection': ['umap-learn>=0.5'],
    'test': ['pytest>=6.2.2', 'hypothesis>=6.87.0'],
}
extras_require['test'] = sorted(set(extras_require['test']) | set(extras_require['embedding']) | set(extras_require['clustering']))
extras_require['all'] = sorted({dep for deps in extras_require.values() for dep in deps})

setup(
    name='infodynamics',
    version=_read_version(),
    packages=find_packages(),
    url='https://github.com/jankounchained/infodynamics/',
    project_urls={
        'Source': 'https://github.com/jankounchained/infodynamics',
        'Issues': 'https://github.com/jankounchained/infodynamics/issues',
    },
    license='MIT',
    author='Jan Kostkan',
    description=(
        'Novelty, transience and resonance signals for numeric time series, '
        'with an optional text on-ramp.'
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.14',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.14',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Text Processing :: Linguistic',
    ],
    install_requires=[
        'numpy>=1.19.0',
        'matplotlib>=3.3.2',
        'scikit-learn>=1.3.0',
        'syntok>=1.4.4',
        'typing-extensions>=4.8.0',
    ],
    extras_require=extras_require,
)