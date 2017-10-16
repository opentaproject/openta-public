# OpenTA
A web-based platform for E-learning. Consists of a Python backend together with a web front end. Try it out by running the django development server locally (see below). 

## [Installation](docs_src/installation/development.rst)

## Quick start with docker
Install [Docker](https://docs.docker.com/engine/installation/).


Clone the repository to a local folder
```
git clone https://github.com/hlinander/openta.git
```

and configure backend and frontend settings from the template files (```settings_dev.py``` and ```settings_example.js```), for a simple single site installation you can copy the templates to ```settings.py``` and ```settings.js``` (for details see installation instructions above).

Copy the example database from ```django/backend/db.sqlite3.example``` to ```django/backend/db.sqlite3```.

Change workdirectory ```cd docker```. To build the Docker image run (grab a coffee)
```
make image
```

To start the server
```
make serve
```
which will now be available at ```localhost:8000```. To serve and watch for file changes in the code use
```
make watch
```

Stop the server by multiple **Ctrl-C** till you are back at your shell. Use ```make serve port=4000``` (and similar for watch) to use another port.

When cloning this repository a file based sqlite database is provided with two users (user:password):
* teacher:learning, can edit exercises via the author interface.
* student:learning, can view and answer exercises.

## [Exercise format](docs_src/author/exercise_xml.rst)
## Question types
- [compareNumeric](docs_src/author/questiontypes/comparenumeric.rst)
