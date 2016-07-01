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
  config: {cors: true},
  handler: (request, reply) => {
    var json = showExercise('./exercises/' + request.params.name + '/problem.xml');
    reply(json);
  }
});

server.route({
  method: 'GET',
  path: '/exercises',
  config: {cors: true},
  handler: (request, reply) => reply(listExercises())
});

server.register(require('inert'), err => {
  if(err) {
    throw err;
  }

  server.route({
    method: 'GET',
    path: '/exercise/{name}/{asset}',
    handler: (request, reply) => {
      reply.file('./exercises/' + request.params.name + '/' + request.params.asset);
    }
  });
});

server.start( (err) => {
  if(err) {
    throw err;
  }
  console.log('Server running at:', server.info.uri);
});
