===================
Contributing Guide
===================

=================
Development Setup
=================

1. Clone the repository and set up the development environment:

   .. code-block:: bash

      # Clone the repository
      git clone https://github.com/user/lifecyclelogging.git
      cd lifecyclelogging

      # Install development dependencies
      pip install -e ".[dev,test,docs]"
      pip install nox

============
Code Quality
============

Run all checks before submitting changes:

.. code-block:: bash

   # Run all checks
   make check

Individual checks can be run with:

.. code-block:: bash

   # Format code
   make format

   # Run linting
   make lint

   # Run type checking
   make type

========
Testing
========

Run the test suite:

.. code-block:: bash

   # Run all tests
   make test

   # Run tests with coverage report
   make test-coverage

==============
Documentation
==============

Build and view documentation:

.. code-block:: bash

   # Build documentation
   make docs

   # Serve documentation locally
   make docs-serve

=======================
Pull Request Guidelines
=======================

1. Create a feature branch from "main"
2. Update documentation for any new features
3. Add tests for new functionality
4. Ensure all checks pass:
   - Code formatting ("make format")
   - Linting ("make lint")
   - Type checking ("make type")
   - Tests ("make test")
5. Submit a pull request

=================
Development Tools
=================

- **Nox**: Handles test automation and environment management
- **Ruff**: Code linting and formatting
- **MyPy**: Static type checking
- **Pytest**: Testing framework
- **Sphinx**: Documentation generation

The project uses modern Python tooling:

- Type hints for better code quality
- Ruff for consistent code style
- MyPy for static type checking
- Pytest for comprehensive testing
