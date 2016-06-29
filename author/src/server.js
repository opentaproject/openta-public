'use strict';

const Hapi = require('hapi');

//Project imports
import { listExercises, showExercise } from "./api/exercises.js";

const server = new Hapi.Server();
server.connection({
  host: 'localhost',
  port: 8000
});

server.route({
  method: 'GET',
  path: '/hello',
  handler: (request, reply) => reply('hello world')
});

server.route({
  method: 'GET',
  path: '/exercise/{name}',
  handler: (request, reply) => {
    var json = showExercise('./exercises/' + request.params.name);
    reply(json);
  }
});

server.route({
  method: 'GET',
  path: '/exercises',
  config: {cors: true},
  handler: (request, reply) => reply(listExercises())
});

server.start( (err) => {
  if(err) {
    throw err;
  }
  console.log('Server running at:', server.info.uri);
});
