# Setting up a Development Environment

You can set up a development environment for the project either by using `pip` or `poetry`. Pip is a package
management system for Python. One drawback to using pip is that upgrading packages is not simple. Poetry
offers a dependency management system for Python projects among other things.

## Using pip

### Initial Installation

Follow these instructions to set up the development environment using *pip*.

1. Create a Python virtual environment for the Django project by entering the following commands in a *shell*:

    ```sh
    cd __project_root__/django
    python3 -m venv env
    source env/bin/activate
    ```

    The last command activates the Python virtual environment.

1. Install the project's dependencies:

    ```sh
    pip install -r requirements.txt
    pip install -r requirements_dev.txt
    ```

    This command may take a while to complete since it is downloading Python packages over the internet.

###   Working on the Project

1. Adding a new project dependency:

    ```sh
    cd __project_root__/django
    pip install __new_package_name__
    pip freeze | grep -v "pkg-resources" > requirements.txt
    ```

1. To deactivate the Python virtual environment:

    ```sh
    deactivate
    ```

## Using Poetry

### Initial Installation

Follow these instructions to set up the development environment using *poetry*.

1. Install poetry.

    ```sh
    curl -sSL https://install.python-poetry.org | python3 -
    ```

    Follow the instructions shown by the above command to add poetry to your `$PATH`.

1. Verify that poetry was installed.

    ```sh
    poetry --version
    ```

1. Configure poetry to create virtual environments in a project's root directory.

    ```sh
    poetry config virtualenvs.in-project true
    ```

    Not doing this results in virtual environments being created in the home directory.

### Working on the Project

1. To create the project's virtual environment and install project dependencies:

    ```sh
    cd __project_root__/django
    poetry install
    ```

1. To update project dependencies:

    ```sh
    cd __project_root__/django
    poetry update
    ```

1. To add a new project dependency, two options are available:

    * add a dependency that is required to run on the production version of the server:

        ```sh
        cd __project_root__/django
        poetry add __new_package_name__
        ```

    * add a dependency that is required only in a development environment:

        ```sh
        cd __project_root__/django
        poetry add --dev __new_package_name__
        ```

        For example, the `pytest` package is only required in a development environment.

1. To remove a project dependency:

    ```sh
    cd __project_root__/django
    poetry remove __package_name__
    ```

1. To start a shell using the Python virtual environment:

    ```sh
    cd __project_root__/django
    poetry shell
    ```

1. To run the test suite when not in a virtual environment:

    ```sh
    cd __project_root__/django/backup
    poetry run  pytest -m "not end_to_end"
    ```

    To run the test suite for a single Django application:

   ```sh
   cd __project_root__/django/backup
   poetry run  pytest __app_name__
   ```

   Where `__app_name__` can be one of: `course`, `translations`, `exercises`, etc.

1. To show the project's dependency tree:

    ```sh
    poetry show --tree
    ```

1. To deactivate the Python virtual environment:

    ```sh
    deactivate
    ```
