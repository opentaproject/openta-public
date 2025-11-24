import { List, Set } from 'immutable';
const isList = List.isList;

function keyIn(...keys) {
  var keySet = Set(keys);
  return function (v, k) {
    return keySet.has(k);
  };
}

function logImmutable(x) {
  console.log(JSON.stringify(x, null, 4));
  return x;
}

function mergeNotLists(a, b) {
  if (a && a.mergeWith && !isList(a) && !isList(b)) {
    return a.mergeWith(merger, b);
  }
  return b;
}

//Returns an immutable list if the object is not an immutable List or javascript Array
function enforceList(a) {
  if (!isList(a) && !Array.isArray(a)) {
    return List([a]);
  } else {
    return a;
  }
}

export { logImmutable, mergeNotLists, enforceList, keyIn };
