'use strict';
var fs = require('mz/fs');
var xml2js = require('xml2js');
var xmlparser = new xml2js.Parser({trim:true});
var _ = require('lodash');
import { compareExpressions, toLatex } from './symbolic.js'; 


function consoleJSON(obj) {
  console.log(JSON.stringify(obj, null, 4));
}

function parseXML(xml) {
  return new Promise( (resolve, reject) => {
    xmlparser.parseString(xml, (err, result) => {
      if(err) reject(err);
      resolve(result);
    });
  });
}
// () => List
// List available exercises
export function listExercises() {
  return fs.readdir("./exercises/").catch( err => console.log(err) );
}

export function getExerciseXMLasJSON(exercise) {
  var parser = new xml2js.Parser();
  var problemdata = fs.readFile(exercise, 'utf8')
    //.then( file => { console.log(file); return file;} )
    .then( parseXML )
    //.then( data => { consoleJSON(data); return data; } )
    .catch( err => console.log(exercise + ': ' + err) );
  return problemdata;
}

function parseIngress(ingress) {
  try{ 
    var variables = ingress.split(';')
  .filter( x => x !== "" )
  .map( x => x.split('=') )
  .map( x => ({ name: x[0].trim(), value: x[1].trim() }) );
  return variables;
  } catch(err) {
    console.dir(err);
    return {}
  }
}

export function checkQuestion(exercise, question, expression) {
  return getExerciseXMLasJSON('./exercises/' + exercise + '/problem.xml')
  .then(json => {
    if(_.has(json,'problem.thecorrectanswer[' + question + ']')) {
      var correct = json.problem.thecorrectanswer[question]._
      .replace(';', '');
      //Parse ingress
      try {
        var variables = parseIngress(json.problem.thecorrectanswer[0]._);
      console.log(expression);
        return Promise.all(
          [
            compareExpressions(JSON.stringify(variables), correct, expression),
            toLatex(expression)
          ])
          .then( res => ({ equal: res[0], latex: res[1] }) );
      } catch(err) {
        console.dir(err)
        return {
          error: err
        }
      }
    }
    else {
      return {error: 'Cannot extract question ' + question + ' from exercise ' + exercise};
    }
  });
}
