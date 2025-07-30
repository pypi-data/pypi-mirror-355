# ddnnife-cli
This package provides a CLI wrapper for the [ddnnife](https://github.com/SoftVarE-Group/d-dnnf-reasoner) Docker container.

## Usage
We recommend using `ddnnife-cli` in a virtual environment.

```python
python3 -m venv .venv
source .venv/bin/activate
pip install ddnnife-cli
```

Afterwards, you can run `ddnnife-cli` via

* `ddnnife-cli`
* `python -m ddnnife_cli`


In the case that the default [image and tag](ghcr.io/softvare-group/ddnnife:main-amd64) (`ghcr.io/softvare-group/ddnnife:main-amd64`) cannot be found on your system, `ddnnife-cli` can pull it for you. You may also specify `--image` and `--tag` to use another image and tag.

Afterwards, you can use `ddnnife` as described in its [documentation](https://github.com/SoftVarE-Group/d-dnnf-reasoner/?tab=readme-ov-file#usage). For instance to count the number of satisfying solutions in a DIMACS file:

```bash
ddnnife-cli --input <your-input-file>.dimacs
```

Or to compute a uniform random sample of size 1024:

```bash
ddnnife-cli --input <your-input-file>.dimacs -- urs -n 1024
```