[![Pytest](https://github.com/DataShades/ckanext-blocksmith/actions/workflows/test.yml/badge.svg)](https://github.com/DataShades/ckanext-blocksmith/actions/workflows/test.yml)

Blocksmith is a CKAN extension that allows you to create and manage pages using a visual editor.

![editor screenshot](https://raw.githubusercontent.com/DataShades/ckanext-blocksmith/master/docs/images/editor.png)

![list screenshot](https://raw.githubusercontent.com/DataShades/ckanext-blocksmith/master/docs/images/list.png)

Check full [documentation](https://datashades.github.io/ckanext-blocksmith/) for more information.

## Requirements

CKAN 2.10+
Python 3.10+

## Installation

Install it from source:
    ```
    pip install -e .
    ```

Or use `pypi` to install:
    ```
    pip install ckanext-blocksmith
    ```

Initialize DB tables by running ```ckan -c PATH_TO_CONFIG db upgrade -p blocksmith```

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
