// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import { absify } from './QuestionLinearAlgebra.jsx';

test('absify', () => {
  expect(absify('|a+b|')).toBe('Norm(a+b)');
  expect(absify('|a+b')).toBe('|a+b');
  expect(absify('||a+b|*c|')).toBe('Norm(Norm(a+b)*c)');
});
