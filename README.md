# infodynamics

[![Release](https://img.shields.io/github/v/release/jankounchained/infodynamics)](https://img.shields.io/github/v/release/jankounchained/infodynamics)
[![Build status](https://img.shields.io/github/workflow/status/jankounchained/infodynamics/merge-to-main)](https://img.shields.io/github/workflow/status/jankounchained/infodynamics/merge-to-main)
[![codecov](https://codecov.io/gh/jankounchained/infodynamics/branch/main/graph/badge.svg)](https://codecov.io/gh/jankounchained/infodynamics)
[![Commit activity](https://img.shields.io/github/commit-activity/m/jankounchained/infodynamics)](https://img.shields.io/github/commit-activity/m/jankounchained/infodynamics)
[![Docs](https://img.shields.io/badge/docs-gh--pages-blue)](https://jankounchained.github.io/infodynamics/)
[![Code style with black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports with isort](https://img.shields.io/badge/%20imports-isort-%231674b1)](https://pycqa.github.io/isort/)
[![License](https://img.shields.io/github/license/jankounchained/infodynamics)](https://img.shields.io/github/license/jankounchained/infodynamics)

Windowed average relative entropies conviniently wrapped in a sklearn-like API

- **Github repository**: <https://github.com/jankounchained/infodynamics/>
- **Documentation** <https://jankounchained.github.io/infodynamics/>

## Getting started with your project

First, create a repository on GitHub with the same name as this project, and then run the following commands:

``` bash
git init -b main
git add .
git commit -m "init commit"
git remote add origin git@github.com:jankounchained/infodynamics.git
git push -u origin main
```

Finally, install the environment and the pre-commit hooks with 

```bash
make install
```

You are now ready to start development on your project! The CI/CD
pipeline will be triggered when you open a pull request, merge to main,
or when you create a new release.

To finalize the set-up for publishing to PyPi or Artifactory, see
[here](https://fpgmaas.github.io/cookiecutter-poetry/features/publishing/#set-up-for-pypi).
For activating the automatic documentation with MkDocs, see
[here](https://fpgmaas.github.io/cookiecutter-poetry/features/mkdocs/#enabling-the-documentation-on-github).
To enable the code coverage reports, see [here](https://fpgmaas.github.io/cookiecutter-poetry/features/codecov/).

## Releasing a new version

- Create an API Token on [Pypi](https://pypi.org/).
- Add the API Token to your projects secrets with the name `PYPI_TOKEN` by visiting 
[this page](https://github.com/jankounchained/infodynamics/settings/secrets/actions/new).
- Create a [new release](https://github.com/jankounchained/infodynamics/releases/new) on Github. 
Create a new tag in the form ``*.*.*``.

For more details, see [here](https://fpgmaas.github.io/cookiecutter-poetry/releasing.html).

---

Repository initiated with [fpgmaas/cookiecutter-poetry](https://github.com/fpgmaas/cookiecutter-poetry).