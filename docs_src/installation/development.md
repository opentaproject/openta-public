# Development
## Note on login information

When cloning this repository a file based sqlite database is provided with two users (user:password):
* teacher:learning, can edit exercises via the author interface.
* student:learning, can view and answer exercises.

## Development environment using Docker 

Start by cloning the repository

```
git clone https://github.com/hlinander/openta.git
```

Install [Docker](https://docs.docker.com/engine/installation/) and configure backend and frontend settings from the template files (```settings_dev.py``` and ```settings_example.js```) as shown below.

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


## Manual installation
### Backend Installation
The following will assume the repository is cloned into a folder ```openta/```.

Requires: 
* [Python 3](https://www.python.org)
* libjpeg
* libgraphivz
* libcairo2
* graphviz
* libxml2
* libxslt1
* python-dev
* libzmq-dev

In an apt-based linux distribution the required dependencies can be installed with
```
apt get install libjpeg-dev libgraphviz-dev graphviz pkg-config libxml2-dev libxslt1-dev python-dev libzmq3-dev libcairo2 libcairo2-dev
```

#### Steps

Enter the backend subfolder with ```cd django```.
Create a python 3 environment in a subdirectory ```env``` (name not important) with
```
virtualenv env
```
or
```
pyvenv env
```
depending on your installation. You might need to add an argument ```-p python3``` with the path to your python3 binary.

Enter the environment with
```
source env/bin/activate
```

Install all dependencies with (on some systems you might need ```pkg-config``` installed for the python build scripts to find some of the library dependencies)
```
pip install -r requirements.txt
```

Choose a version of the django settings file located in
```
django/backend/backend/
```
For local development the ```settings_dev.py``` would be suitable.
Copy the choosen file to ```settings.py```, for example
```
cd backend/backend/
cp settings_dev.py settings.py
```

Start development server with
```
cd ..
python manage.py runserver
```

#### Summary of third party libraries
* [Django](https://www.djangoproject.com/) 
* [Django-rest-framework (DRF)](http://www.django-rest-framework.org/)
* [Sympy](http://www.sympy.org/)

### Front-end installation
A web frontend for viewing/editing exercises served by the backend.

Requires: 
* [NodeJS (>6.0) & NPM](https://nodejs.org) package system
* [Brunch](http://brunch.io/): A html/js build tool used during development
(can be installed systemwide with ```npm install -g brunch``` (needs sudo if on *nix))

Install all dependencies (specified in package.json) with
```
cd frontend
npm install
```

Make a local copy of the settings file (for local development no changes are needed) with
```
cd frontend/app/
cp settings_example.js settings.js
```

Build frontend and copy the bundle to the django server (as specified in brunch-config.js)
```
cd frontend
brunch build
```
Alternatively, start a live-development watcher that recompiles and copies the files whenever something changes
```
brunch watch
```

#### Summary of third party libraries
* [React](https://facebook.github.io/react/): JS GUI framework
* [Redux](http://redux.js.org/): State management library
* [UIKit](http://getuikit.com/): CSS framework
