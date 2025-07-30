.. image:: https://img.shields.io/pypi/v/jaraco.logging.svg
   :target: https://pypi.org/project/jaraco.logging

.. image:: https://img.shields.io/pypi/pyversions/jaraco.logging.svg

.. image:: https://github.com/jaraco/jaraco.logging/actions/workflows/main.yml/badge.svg
   :target: https://github.com/jaraco/jaraco.logging/actions?query=workflow%3A%22tests%22
   :alt: tests

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Ruff

.. image:: https://readthedocs.org/projects/jaracologging/badge/?version=latest
   :target: https://jaracologging.readthedocs.io/en/latest/?badge=latest

.. image:: https://img.shields.io/badge/skeleton-2025-informational
   :target: https://blog.jaraco.com/skeleton

Argument Parsing
================

Quickly solicit log level info from command-line parameters::

    parser = argparse.ArgumentParser()
    jaraco.logging.add_arguments(parser)
    args = parser.parse_args()
    jaraco.logging.setup(args)
