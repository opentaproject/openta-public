// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import { lazy } from 'react';
const questionDispatch = {
  //'compareNumeric': QuestionCompareNumeric,
  //'none': 'div'
};

function registerQuestionType(type, component) {
  questionDispatch[type] = component;
}

export { questionDispatch, registerQuestionType };
