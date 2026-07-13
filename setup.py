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
extras_require['all'] = sorted({dep for deps in extras_require.values() for dep in deps})

setup(
    name='infodynamics',
    version=_read_version(),
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
    entry_points={
        'console_scripts': [
            'infodynamics-pack=infodynamics.shipping:pack_main',
            'infodynamics-pull=infodynamics.shipping:pull_main',
            'infodynamics-verify=infodynamics.shipping:verify_main',
            'infodynamics-init-project=infodynamics.shipping:init_project_main',
        ],
    },
)