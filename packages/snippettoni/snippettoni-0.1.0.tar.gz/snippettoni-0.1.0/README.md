[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/snippettoni)](https://pypi.org/project/snippettoni/)


![Snippettoni](https://raw.githubusercontent.com/ffaraone/snippettoni/main/assets/snippettoni.png)


# 🍝 Snippettoni

**Snippettoni** is a Python library that helps you generate the `x-codeSamples` extension for OpenAPI specifications. It supports multiple programming languages and allows you to use custom templates or extend the library with your own logic. Inspired by the deliciousness of "maccheroni" and the elegance of code snippets, Snippettoni serves up tasty examples for your API documentation.



## Install

```sh
$ pip install snippettoni
```


## Usage

```sh
$ snippettoni --output enriched_openapi_spec.yaml openapi_spec.yaml
```

```sh
$ snippettoni --help

 Usage: snippettoni [OPTIONS] SPEC_PATH

╭─ Arguments ─────────────────────────────────────────────────────────────╮
│ *    spec_path      PATH  Path to OpenAPI spec YAML or JSON file.       │
│                           [default: None]                               │
│                           [required]                                    │
╰─────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────╮
│ --base-url                  TEXT  Base URL for code examples.           │
│                                   [default: None]                       │
│ --lang                      TEXT  Languages to generate (e.g. --lang    │
│                                   python --lang curl).Default is all    │
│                                   templates in directory.               │
│                                   [default: None]                       │
│ --template                  TEXT  Override or add templates per         │
│                                   language, e.g. --template lang:path   │
│                                   [default: None]                       │
│ --output                    PATH  Optional output file path. Defaults   │
│                                   to stdout in same format as input.    │
│                                   [default: None]                       │
│ --install-completion              Install completion for the current    │
│                                   shell.                                │
│ --show-completion                 Show completion for the current       │
│                                   shell, to copy it or customize the    │
│                                   installation.                         │
│ --help                            Show this message and exit.           │
╰─────────────────────────────────────────────────────────────────────────╯

```

## License

Snippettoni is licensed under Apache 2.0 License.
