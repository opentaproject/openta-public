# OpenTA
A web-based platform for E-learning. Consists of a Python backend together with a web front end. Try it out by running the django development server locally (see below). 

When cloning this repository a file based sqlite database is provided with two users (user:password):
* teacher:learning, can edit exercises via the author interface.
* student:learning, can view and answer exercises.

## Backend Installation
The following will assume the repository is cloned into a folder ```openta/```.

Requires: 
* [Python 3](https://www.python.org)

Enter the backend subfolder with ```cd django```.
Create a python 3 environment in a subdirectory ```env``` (name not important) with
```
virtualenv env
```
Enter the environment with
```
source env/bin/activate
```

Install all dependencies with
```
pip install -r requirements.txt
```

Start development server with
```
cd backend
python manage.py runserver
```

### Summary of third party libraries
* [Django](https://www.djangoproject.com/) 
* [Django-rest-framework (DRF)](http://www.django-rest-framework.org/)
* [Sympy](http://www.sympy.org/)

## Front-end installation
A web frontend for viewing/editing exercises served by the backend.

Requires: 
* [NPM](https://nodejs.org) package system
* [Brunch](http://brunch.io/): A html/js build tool used during development
(can be installed systemwide with ```npm install -g brunch``` (needs sudo if on *nix))

Install all dependencies (specified in package.json) with
```
cd author_frontend
npm install
```
Build frontend and copy the bundle to the django server (as specified in brunch-config.js)
```
brunch build
```
Alternatively, start a live-development watcher that recompiles and copies the files whenever something changes
```
brunch watch
```

### Summary of third party libraries
* [React](https://facebook.github.io/react/): JS GUI framework
* [Redux](http://redux.js.org/): State management library
* [UIKit](http://getuikit.com/): CSS framework
