import os
from setuptools import setup, find_packages


directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='infodynamics',
    version='0.0.1',
    packages=find_packages(),
    url='https://github.com/centre-for-humanities-computing/infodynamics/',
    license='CC-BY',
    author='Jan K',
    description='Ahoj',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'numpy>=1.19.0',
        'matplotlib>=3.3.2',
        'scipy>=1.5.2',
        'pytest>=6.2.2'
    ]
)