# OpenTA
A web-based platform for E-learning. Consists of a Python backend together with a web front end. Try it out by running the django development server locally (see below). 

When cloning this repository a file based sqlite database is provided with two users (user:password):
* teacher:learning, can edit exercises via the author interface.
* student:learning, can view and answer exercises.

## Backend Installation
The following will assume the repository is cloned into a folder ```openta/```.

Requires: 
* [Python 3](https://www.python.org)
* libjpeg
* libgraphivz
* graphviz
* libxml2
* libxslt1
* python-dev

In an apt-based linux distribution the required dependencies can be installed with
```
apt get install libjpeg-dev libgraphviz-dev graphviz pkg-config libxml2-dev libxslt1-dev python-dev
```

### Steps

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

### Summary of third party libraries
* [Django](https://www.djangoproject.com/) 
* [Django-rest-framework (DRF)](http://www.django-rest-framework.org/)
* [Sympy](http://www.sympy.org/)

## Front-end installation
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
 
## Exercise format
An exercise consists of a directory containing a definition file ```exercise.xml``` together with a file ```exercisekey``` and possibly additional assets such as figures/pdf.

### ```exercisekey```
Contains a unique key (up to 255 bytes of UTF8 encoded ASCII) that identifies the exercise to the database. A key file can be added and assigned manually, but is automatically generated as a [uuid4](https://docs.python.org/3.5/library/uuid.html) identifier if not present.

### ```exercise.xml```
Contains all exercise data, a typical example: 
```xml
<exercise>
  <exercisename>...</exercisename>
  <figure>...</figure>
  <exercisetext>...</exercisetext>
  
  <question key=... type=...>
    ....
  </question>
</exercise>
```

### Tags
| Tag       | Attributes | Description |
| ---       | ---------- | ----------- |
| ```exercise```  | None           | Root tag  |
| ```exercisename``` | | The visible name/title of the exercise |
| ```question``` | ```key``` = unique id (within the exercise), ```type``` = question type (see ...) | Question root tag |

## Question types
### compareNumeric
Compares two symbolic expressions numerically by evaluation.
Example:
```
<question type="compareNumeric">
 <variables>x=3; y=7;</variables>
 <text>What is the derivative with respect to $x$ of $x^2*y$?</text>
 <expression>2*x*y</expression>
</question>
```
### Subtags
| Tag       | Attributes | Description |
| ---       | ---------- | ----------- |
| ```text``` | | Question text |
| ```variables```| | Variables in semicolon separated list of var=value, e.g. "x=1;y=2;" |
| ```expression```| | Correct expression |
