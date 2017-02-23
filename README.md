# OpenTA
A web-based platform for E-learning. Consists of a Python backend together with a web front end. Try it out by running the django development server locally (see below). 

## [Installation](docs_src/installation/development.md)

## Quick start with docker

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

When cloning this repository a file based sqlite database is provided with two users (user:password):
* teacher:learning, can edit exercises via the author interface.
* student:learning, can view and answer exercises.

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

