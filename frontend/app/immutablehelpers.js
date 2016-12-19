import { List } from 'immutable'
const isList = List.isList

function logImmutable(x) {
  console.log(JSON.stringify(x, null, 4));
  return x;
}

function mergeNotLists(a, b) {
  if (a && a.mergeWith && !isList(a) && !isList(b)) {
    return a.mergeWith(merger, b)
  }
  return b
}

export { logImmutable, mergeNotLists }
