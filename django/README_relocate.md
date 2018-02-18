# Moving installation
To guarantee a working python environment you should remake the environment on moving the OpenTA
installation. First remove the old venv with
```rm -r env_name```
and then remake using either virtualenv or venv package using requirements.txt.

# Relocate virtual environment
To be able to move the installation without remaking the virtual environment after the installation
is done:

```virtualenv --relocatable env_name```

then edit ```env_name/bin/activate``` and

set ```VIRTUAL_ENV``` to the proper path.

Note that this is subject to change in the virtualenv package, from the virtualenv documentation:

"The --relocatable option currently has a number of issues, and is not guaranteed to work in
all circumstances. It is possible that the option will be deprecated in a future version of
virtualenv."