## Mango Pycore

An implementation of common features for all SAM backend projects for [Mango Soft Inc](http://www.mango-soft.com)

### How to install

```bash
    $ pip install mango-pycore
```

### Documentation 
To view the documentation in your own machine:
Got to docs/_build/html and view the index.html file (open with live server).

### Create Documentations from Scratch 
Make sure you are working on a virtual environment with Sphinx installed:
(using python 3.9)

```bash
    $ python3 --version
    Python 3.9.7
    $ python3 -m venv venv39
    $ . venv39/bin/activate
```
Install Sphinx and the Sphinx rtd theme:

```bash
    $ pip install -U sphinx
    $ pip install sphinx-rtd-theme
```

Create a docs folder inside the "api" folder:

```bash
    $ mkdir docs
```

Inside the docs folder, start sphinx:

```bash
    $ sphinx-quickstart
```

Fill the documentation information: your name, the project's name and the release number.
Let the language and the separation of the source as default: [eng] an [no].

Go into the "conf.py" document insid the docs folders.
Add the desired path after importing os and sys:

```python
    import os
    import sys
    sys.path.insert(0, os.path.abspath('..'))
```

Modify the extensions:

```python
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx.ext.viewcode", "sphinx.ext.todo"]
autodoc_default_options = {
    
    'members': True,
    'undoc-members': False,
    'private-members': True,
    'special-members': False,
    'inherited-members': False,
    'show-inheritance': False,
}
```
Select the desired theme, in this case we will be using the "sphinx rtd theme":

```python
    html_theme = 'sphinx_rtd_theme'
```

In the main folder of the project run:

```bash
    $ sphinx-apidoc -o docs folder_you_want_documented
```
This will create the .rst files for the documentation of the folder you want to document. The .rst files will
appear in the docs folder.

Make sure the modules.rst file references the modules inside your project.
In our case it should look like this:
```python
    mango_pycore
============

.. toctree::
   :maxdepth: 4

   api
   environment_data
   objects
   stream
   tools
   websocket

```
Inside the docs folder run:
```bash
    make html
```

Modify the .rst files to your convenience.












