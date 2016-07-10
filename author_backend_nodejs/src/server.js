'use strict';

const Hapi = require('hapi');

//Project imports
import { listExercises, getExerciseXMLasJSON, getExerciseXML, checkQuestion } from "./api/exercises.js";
import { initSymbolic } from "./api/symbolic.js";

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
    var json = getExerciseXMLasJSON('./exercises/' + request.params.name + '/problem.xml');
    reply(json);
  }
});

server.route({
  method: 'GET',
  path: '/exercise/{name}/xml',
  config: {cors: true},
  handler: (request, reply) => {
    var XML = getExerciseXML('./exercises/' + request.params.name + '/problem.xml');
    reply(XML);
  }
});

server.route({
  method: 'POST',
  path: '/exercise/{name}/question/{num}/check',
  config: {
    cors: true/*{
            origin: ['*'],
            additionalHeaders: ['*']
        }*/
  },
  handler: (request, reply) => {
    var json = JSON.parse(request.payload.json);
    var result = checkQuestion(request.params.name, request.params.num, json.expression)
    .then( res => { console.dir(res); return res; } );
    reply(result);
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
    path: '/exercise/{name}/asset/{asset}',
    handler: (request, reply) => {
      reply.file('./exercises/' + request.params.name + '/' + request.params.asset);
    }
  });
});

initSymbolic();

server.start( (err) => {
  if(err) {
    throw err;
  }
  console.log('Server running at:', server.info.uri);
});
