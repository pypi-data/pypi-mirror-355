# Piewuita

This is a library to init a python projects.

## Features

* Automatically create a project directory with:
    * main.py
    * readme.md
    * .gitignore
* Initializes a virtual environment (venv) in the project.
* Installs specified python modules and generates a `requirements.txt` file.
* Sets up Git in the project directory.

## Installation

### Install the library

```bash
pip install piewuita
```

### Install to development

```bash
git clone git@github.com:Fuan200/piewuita.git
cd piewuita
# optional create a virtual environment
pip install -e .
```

### Pip with repo

``` bash
pip install git+https://github.com/Fuan200/piewuita.git
```

## Usage

The `piewuita` CLI simplifies project initialization. Use the following command to create a new project:

``` bash
piewuita -n <project_name> [-m <module1> <module2> ...]
```

* `-n, --name` (required): The name of the project.
* `-m, --modules` (optional): A space-separated list of Python modules/libraries to install in the `venv`.

#### Examples

``` bash
piewuita -n new_project
```

``` bash
piewuita -n new_project -m Flask requests pandas
```

## Requirements

* Python 3
* Git

## OS

* Linux
* MacOS ?

## Author

:blue_heart: **Juan Díaz** - [Fuan200](https://github.com/Fuan200)