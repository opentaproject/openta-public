// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import reducer from '../reducers.js';
import * as actions from '../actions.js';

test('reducer', () => {
  it('should return the initial state', () => {
    expect(reducer(undefined, {})).toEqual(
      immutable.fromJS({
        exercises: [],
        folder: '',
        activeExercise: '',
        activeAdminTool: 'xml-editor',
        exerciseState: {}
      })
    );
  });

  it('should handle UPDATE_EXERCISE_STATE', () => {
    var action1 = actions.updateExerciseState('key', {
      question: {
        1: {
          prop: 'val'
        }
      }
    });
    var action2 = actions.updateExerciseState('key', {
      question: {
        2: {
          prop: 'val'
        }
      }
    });
    var action3 = actions.updateExerciseState('key', {
      question: {}
    });
    expect(reducer(reducer(reducer({}, action1), action2), action3)).toEqual(
      immutable.fromJS({
        exerciseState: {
          key: {
            question: {
              1: { prop: 'val' },
              2: { prop: 'val' }
            }
          }
        }
      })
    );
  });
});
