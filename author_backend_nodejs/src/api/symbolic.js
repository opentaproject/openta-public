var rpc = require('zerorpc');

var client;

export function initSymbolic() {
  try {
    client = new rpc.Client();
    client.connect("tcp://0.0.0.0:4242");
    //client.invoke("evaluate", '[{"name": "x", "value": 2}, {"name": "y", "value": 3}]', "x*y", (err, res, more) => {
      //console.log(res);
    //});
  }
  catch(err) {
    console.log(err);
  }
}

export function compareExpressions(variables, expression1, expression2) {
  return client.invoke("compareExpressions", variables, expression1, expression2);
}

//export function parse
