# OpenTA
# Author
A (to be) self contained package for local development of exercises. In the current version it consists of a backend (**author_backend_nodejs**) serving the exercises and a frontend (**author_frontend**) for viewing the rendered exercises in a browser.
## Author backend (nodejs version)
A nodejs module serving exercises from the filesystem.
### Installation
Requires: [NPM](https://nodejs.org) package system.

Install all dependencies (specified in package.json) with
```
cd author_backend_nodejs
npm install
```
Compile and run with
```
npm run bstart
```
### Summary of third party libraries
* [Hapi](http://www.hapijs.com): A server framework with routing
* [xml2js](https://github.com/Leonidas-from-XIV/node-xml2js): XML parser

## Author frontend
A web frontend for viewing exercises served by the backend.

### Installation
Requires: 
* [NPM](https://nodejs.org) package system
* [Brunch](http://brunch.io/): A html/js build tool used during development
(can be installed systemwide with ```npm install -g brunch``` (needs sudo if on *nix))

Install all dependencies (specified in package.json) with
```
cd author_frontend
npm install
```
Build frontend
```
brunch build
```
Start development server (in the deployed version this will be served by backend)
```
brunch watch --server
```
(This starts a hot reload server, i.e. no need to restart when editing existing source files).
Access in browser at [http://localhost:3333](http://localhost:3333).

### Summary of third party libraries
* [React](https://facebook.github.io/react/): JS GUI framework
* [Redux](http://redux.js.org/): State management library
* [UIKit](http://getuikit.com/): CSS framework
