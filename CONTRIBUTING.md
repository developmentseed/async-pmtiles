# Contributing

Issues and pull requests are more than welcome.

**dev install**

```bash
$ git clone https://github.com/developmentseed/aiopmtiles.git
$ cd aiopmtiles
$ python -m pip install -e .["test","dev","aws","gcp"]
```

You can then run the tests with the following command:

```sh
python -m pytest --cov aiopmtiles --cov-report term-missing
```

**pre-commit**

This repo is set to use `pre-commit` to run *isort*, *flake8*, *pydocstring*, *black* ("uncompromising Python code formatter") and mypy when committing new code.

```bash
$ pre-commit install
```
