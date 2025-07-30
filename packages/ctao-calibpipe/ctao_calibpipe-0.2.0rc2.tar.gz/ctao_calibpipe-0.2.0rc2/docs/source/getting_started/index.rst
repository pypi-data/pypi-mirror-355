.. _getting_started:

***************
Getting Started
***************

Installation for users
======================

Currently the package is under active development. First, create and activate a fresh conda environment

.. code-block:: shell

    mamba create -n calibpipe -c conda-forge python==3.12 ctapipe
    mamba activate calibpipe

and then install `calibpipe` using `pip` and TestPyPI

.. code-block:: shell

    pip install --extra-index-url https://test.pypi.org/simple/ calibpipe


.. _development_setup:

******************
Development Setup
******************

Clone the Source Code
=====================

First, clone the source code from GitLab:

.. code-block:: shell

    git clone https://gitlab.cta-observatory.org/cta-computing/dpps/calibrationpipeline/calibpipe.git
    cd calibpipe

Create and Activate Conda Environment
=====================================

Create and activate an empty conda environment with Python >= 3.10:

.. code-block:: shell

    conda create --name myenv python=3.12
    conda activate myenv

**Note:** For faster environment creation, you can use `mamba`, a drop-in replacement for `conda`:

.. code-block:: shell

    mamba create --name myenv python=3.12
    mamba activate myenv

Perform an Editable Install with pip
====================================

Perform an editable install with pip to include documentation and testing dependencies:

.. code-block:: shell

    pip install -e .[all]

Install Pre-Commit Hooks
========================
To install pre-commit hooks, run:

.. code-block:: shell

    pre-commit install

.. _running_tests:

Running Tests
=============

The tests can be launched manually or in CI (recommended). For some tests, test files might be necessary. Please contact the maintainers to obtain them if needed.

Tests are located in `./src/calibpipe/tests/`. They are divided into two groups: unit tests (`./src/calibpipe/tests/unittests`) and integration tests (`./src/calibpipe/tests/workflows`).
The unit tests can be run with `pytest` either through automatic search or providing a specific file or folder.
To run all tests use `pytest` at any level of `./src/calibpipe/tests/`.

Unit tests can be run without the DB:

.. code-block:: shell

    pytest -v --cov=calibpipe --junitxml=report.xml -m "not gdas and not db and not integration"

The integration tests can be run with any `CWL` runner, compliant with `CWL1.2` or above standard. It is not advised to run them locally.
If you want to set up a local version of integration tests, please contact the maintainers.
