'use strict';
var fs = require('mz/fs');
var xml2js = require('xml2js');
var xmlparser = new xml2js.Parser({trim:true});

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
  //return fs.readdir("../exercises");
  return fs.readdir("./exercises/").catch( err => console.log(err) );
   /* .then( files => {
      console.dir(files);
      return files;
    });  */
  //return files;
}

export function showExercise(exercise) {
  var parser = new xml2js.Parser();
  var problemdata = fs.readFile(exercise, 'utf8')
    .then( file => { console.log(file); return file;} )
    .then( parseXML )
    .then( data => { consoleJSON(data); return data; } )
    .catch( err => console.log(exercise + ': ' + err) );
  return problemdata;
}
