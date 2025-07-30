==========================
Instalation Guide
==========================

Introduction
============

In this Instalation tutorial, you'll use the `mango-pycore` command line utility to install the Mango PyCore framework in your machine. This quickstart uses Python 3.8.

Setting Up Your Environment
===========================

To install Mango Pycore, we’ll first create and activate a virtual environment in Python 3.8:

.. code-block:: bash

    $ python3 --version
    Python 3.8.19
    $ python3 -m venv venv38
    $ . venv38/bin/activate

Next, inside the newly created virtual environment install Mango PyCore using `pip`:

.. code-block:: bash

    $ pip install mango-pycore

Verify the installation
Navigate the virtual environment to find the `site-packages` directory:

.. code-block:: bash

    $ cd venv38/lib/python3.8/site-packages

Run the commmand:

.. code-block:: bash

    $ ls mango_pycore

If everything was intalled properly the directory should contain the following files:

.. code-block:: bash

    __init__.py		environment_data	tools
    __pycache__		objects			websocket
    api			stream

Conclusion
===========================

You have completed the installation tutorial. Next, you can proceed to the `Quickstart-HelloWorld` section to learn more about the Mango PyCore API.