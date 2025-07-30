# pySciTools

A collection of useful tools for scientific computing.

## Installation

You can install the library via pip:

```bash
pip install pySciTools
```

## Usage

```python
from pySciTools import func1, func2

data = [1, 2, 3]
result = func1(data)
print(result)

sum_result = func2(3, 4)
print(sum_result)


```

# Upload to PyPI

```bash
# Install packaging tools
pip install twine setuptools wheel

# Build the package
# Modify the version in setup.py
rm -rf dist build *egg-info
# Remove-Item -Recurse -Force dist, build, *.egg-info

python setup.py sdist bdist_wheel

# Upload the package
# Set up $HOME/.pypirc and create a token
twine upload dist/*


```

## pyproject.toml 构建方式

pyproject.toml 配置项目

```bash
# Install packaging tools
pip install --upgrade setuptools wheel build twine

# Modify the version in setup.py
rm -rf dist *egg-info
Remove-Item -Recurse -Force dist, *.egg-info

python -m build
twine check dist/*
twine upload dist/*


pysci-gpu-test
```
