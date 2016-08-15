function logImmutable(x) {
  console.log(JSON.stringify(x, null, 4));
  return x;
}

export { logImmutable }
