import {absify} from './QuestionLinearAlgebra.jsx'

test('absify', () => {
  expect( absify('|a+b|')).toBe('Norm(a+b)');
  expect( absify('|a+b')).toBe('|a+b');
  expect( absify('||a+b|*c|')).toBe('Norm(Norm(a+b)*c)');
});
