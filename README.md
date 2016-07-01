# OpenTA
# Author
A (to be) self contained package for local development of exercises. In the current version it consists of a backend (author_backend_nodejs) serving the exercises and a frontend (author_frontend) for viewing the rendered exercises in a browser.
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
* [Hapi](http://www.hapi.com): A server framework with routing
* [xml2js](https://github.com/Leonidas-from-XIV/node-xml2js): XML parser

## Author frontend
A web frontend for viewing exercises served by the backend.

(Uses [React](https://facebook.github.io/react/))
