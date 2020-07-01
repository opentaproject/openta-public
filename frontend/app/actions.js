import _ from 'lodash'
import React from 'react';
import ReactDOM from 'react-dom';
import Alert from './components/Alert.jsx';
import immutable from 'immutable';

function updateExerciseFilter(exercisefilter) {
    return {
        type: 'UPDATE_EXERCISEFILTER',
        exercisefilter: exercisefilter,
    };
}

function updateDisplayStyle(displaystyle) {
    return {
        type: 'UPDATE_DISPLAYSTYLE',
        displaystyle: displaystyle
    };
}



function updateLoginStatus(data) {//{{{
  return {
    type: 'UPDATE_LOGIN_STATUS',
    data: data
  }
}//}}}

function setOpenTAVersion(openTAVersion) {
    return {
        type: 'SET_OPENTA_VERSION',
        data: openTAVersion
    }
}

function updateExercises(exercises, folder) {//{{{
  return {
    type: 'UPDATE_EXERCISES',
    exercises: exercises,
    folder: folder
  };
}//}}}

function setExerciseTree(exercisetree, coursePk) {//{{{
  return {
    type: 'SET_EXERCISE_TREE',
    exercisetree: exercisetree,
    coursePk: coursePk
  };
}//}}}

function updateExerciseStatistics(stats) {//{{{
  return {
    type: 'UPDATE_EXERCISE_STATISTICS',
    stats: stats
  };
}//}}}

function updateAggregateStatistics(aggregates) {//{{{
  return {
    type: 'UPDATE_AGGREGATE_STATISTICS',
    aggregates: aggregates
  };
}//}}}

function updateExerciseState(exercise, state) {//{{{
  return {
    type: 'UPDATE_EXERCISE_STATE',
    state: state,
    exercise: exercise
  };
}//}}}

function updateExercisesState(state) {//{{{
  return {
    type: 'UPDATE_EXERCISES_STATE',
    state: state
  };
}//}}}

function updateExerciseJSON(exercise, json) {//{{{
  return {
    type: 'UPDATE_EXERCISE_JSON',
    exercise: exercise,
    json: json
  };
}//}}}

function updateActiveExercise(exercise) {//{{{
  return {
    type: 'UPDATE_ACTIVE_EXERCISE',
    activeExercise: exercise
  };
}//}}}

function updateExerciseXML(exercise, xml) {//{{{
  return {
    type: 'UPDATE_EXERCISE_XML',
    exercise: exercise,
    xml: xml
  };
}//}}}

function updateExerciseActiveXML(exercise, xml) {//{{{
  return {
    type: 'UPDATE_EXERCISE_ACTIVE_XML',
    exercise: exercise,
    xml: xml
  };
}//}}}

function updateQuestionResponse(exerciseKey, questionKey, response) {//{{{
  return {
    type: 'UPDATE_QUESTION_RESPONSE',
    exercise: exerciseKey,
    question: questionKey,
    response: response
  }
}//}}}

function setSavePendingState(exercise, pending) {//{{{
  return {
    type: 'SET_SAVE_PENDING',
    exercise: exercise,
    pending: pending
  }
}//}}}

function setSaveError(exercise, error) {//{{{
  return {
    type: 'SET_SAVE_ERROR',
    exercise: exercise,
    error: error
  }
}//}}}

function setResetPendingState(exercise, pending) {//{{{
  return {
    type: 'SET_RESET_PENDING',
    exercise: exercise,
    pending: pending
  }
}//}}}

function setExerciseModifiedState(exercise, modified) {//{{{
  return {
    type: 'SET_EXERCISE_MODIFIED',
    exercise: exercise,
    modified: modified
  }
}//}}}

function updatePendingState(pendingstate) {//{{{
  console.log("updatePendingState pendingstate = ", pendingstate)
  return {
    type: 'UPDATE_PENDING_STATE',
    pendingstate: pendingstate
  }
}//}}}

function updatePendingStateIn(path, pending) {//{{{
  console.log("updatePendingStateIn pending = ", pending)
  var data = immutable.Map({});
  return {
    type: 'UPDATE_PENDING_STATE',
    pendingstate: data.setIn(path, pending)
  }
}//}}}

function updateActiveAdminTool(tool) {//{{{
  /*
   * Values: xml-editor, options
   */
  return {
    type: 'UPDATE_ACTIVE_ADMIN_TOOL',
    tool: tool
  }
}//}}}

function setImageAnswers(exercise, imageAnswers) {//{{{
  return {
    type: 'SET_IMAGE_ANSWERS',
    exercise: exercise,
    imageAnswers: imageAnswers
  }
}//}}}

function setImageAnswersData(exercise, imageAnswersData) {//{{{
  return {
    type: 'SET_IMAGE_ANSWERS_DATA',
    exercise: exercise,
    imageAnswersData: imageAnswersData
  }
}//}}}

//function updateRegradeResults(exercise,json) {//{{{
//  console.log("updateRegradeResults json = ", JSON.stringify( json  ) )
//  return {
//    type: 'UPDATE_REGRADE_RESULTS',
//    results: json,
//    exercise: exercise
//  }
// }

function updateStudentResults(json) {//{{{
  return {
    type: 'UPDATE_STUDENT_RESULTS',
    results: json
  }
}//}}}

function updateMenuPath(path) {//{{{
  return {
    type: 'UPDATE_MENU_PATH',
    path: path
  }
}//}}}

function updateMenuPathArray(path) {//{{{
  return {
    type: 'UPDATE_MENU_PATH',
    path: immutable.List(path)
  }
}//}}}

function updateMenuLeafDefaults(path, value) {//{{{
  var fullPath = path.concat(['leafDefault']);
  return {
    type: 'UPDATE_MENU_LEAF_DEFAULTS',
    path: fullPath,
    value: value
  }
}//}}}

function updateExercisesReloadMessages(json) {//{{{
  return {
    type:  'UPDATE_EXERCISES_RELOAD_MESSAGES',
    messages: json
  }
}//}}}

function updateAudits(json) {//{{{
  return {
    type: 'UPDATE_AUDITS',
    audits: json
  }
}//}}}

function updateAudit(pk, data) {//{{{
  return {
    type: 'UPDATE_AUDIT',
    audit: pk,
    data: data
  }
}//}}}

function setActiveAudit(pk) {//{{{
  return {
    type: 'SET_ACTIVE_AUDIT',
    audit: pk
  }
}//}}}

function setAuditExerciseStats(exercise, data) {
  return {
    type: 'SET_AUDIT_EXERCISE_STATS',
    exercise: exercise,
    data: data
  }
}

function setActivityRange(range) {//{{{
  return {
    type: 'SET_ACTIVITY_RANGE',
    range: range
  }
}//}}}

function setTableSortField(tableId, field) {//{{{
  return {
    type: 'SET_TABLE_SORT_FIELD',
    tableId: tableId,
    field: field
  }
}//}}}

function setTableSortReverse(tableId, reverse) {//{{{
  return {
    type: 'SET_TABLE_SORT_REVERSE',
    tableId: tableId,
    reverse: reverse
  }
}//}}}

function setResultsFilter(filter) {//{{{
  return {
    type: 'SET_RESULTS_FILTER',
    filter: filter
  }
}//}}}

function setDetailResultsFilter(filter) {//{{{
  return {
    type: 'SET_DETAIL_RESULTS_FILTER',
    filter: filter
  }
}//}}}

function updateStudentDetailResults(userPk, json) {//{{{
  return {
    type: 'UPDATE_STUDENT_DETAIL_RESULTS',
    user: userPk,
    results: json
  }
}//}}}

function setSelectedStudentResults(userPk) {//{{{
  return {
    type: 'SET_SELECTED_STUDENT_RESULTS',
    user: userPk
  }
}//}}}

function setDetailResultExercise(exercise) {//{{{
  return {
    type: 'SET_DETAIL_RESULT_EXERCISE',
    exercise: exercise
  }
}//}}}

function setDetailResultsView(view) {//{{{
  return {
    type: 'SET_DETAIL_RESULTS_VIEW',
    view: view
  }
}//}}}

function updateExerciseTreeUI(tree) {//{{{
  return {
    type: 'UPDATE_EXERCISE_TREE_UI',
    tree: tree
  }
}//}}}

function setExerciseRecentResults(exercise, data) {//{{{
  return {
    type: 'SET_EXERCISE_RECENT_RESULTS',
    exercise: exercise,
    data: data
  }
}//}}}

function setExerciseXMLError(exercise, error) {
  return {
    type: 'SET_EXERCISE_XML_ERROR',
    exercise: exercise,
    error: error
  }
}

function setIFramed(iframed) {
  return {
    type: 'SET_IFRAMED',
    data: iframed
  }
}

export { setOpenTAVersion, updateLoginStatus, updateExercises, setExerciseTree, updateActiveExercise, updateExerciseXML, updateExerciseActiveXML, updateExerciseJSON, updateQuestionResponse, setSavePendingState, setSaveError, setResetPendingState, setExerciseModifiedState, updateExercisesState, updateExerciseState, updatePendingState, updatePendingStateIn, updateActiveAdminTool, setImageAnswers, setImageAnswersData,updateExerciseStatistics, updateMenuPath, updateMenuPathArray, updateMenuLeafDefaults, updateStudentResults, updateExercisesReloadMessages, updateAudits, updateAudit, setActiveAudit, setAuditExerciseStats, updateAggregateStatistics, setActivityRange, setTableSortField, setTableSortReverse, setResultsFilter, updateStudentDetailResults, setSelectedStudentResults, setDetailResultsFilter, setDetailResultExercise, setDetailResultsView, updateExerciseTreeUI, setExerciseRecentResults, setExerciseXMLError, setIFramed, 
updateDisplayStyle, updateExerciseFilter
}

export * from './actions/exercise.js'
export * from './actions/results.js'
export * from './actions/task.js'
export * from './actions/course.js'
export * from './actions/translation.js'
export * from './actions/time.js'
export * from './actions/regrade.js'
