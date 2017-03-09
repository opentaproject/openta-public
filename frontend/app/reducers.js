import immutable from 'immutable';
import {logImmutable, mergeNotLists} from 'immutablehelpers.js';

/*
 *
 * Please remember that the immutable maps makes the proper distinction between integer and string keys whereas javascript dictionaries implicitly converts everything to strings!
 *
 */

var defaultState = immutable.fromJS({ 
  exercises: [], 
  folder: "",
  activeExercise: "",
  activeAdminTool: 'xml-editor',
  menuPath: [],
  menuLeafDefaults: {
    results: {
      //leafDefault: 'list'
    },
    exercises: {
      activity: {
        leafDefault: 'all',
      }
    }
  },
  activityRange: 'all',
  exerciseState: {},
  exerciseTreeUI: {},
  results: {
    studentResults: [],
    filters: {
      text: '',
      requiredKey: 'n_image_deadline',
      bonusKey: 'n_image_deadline',
    },
    detailResultsFilters: {
      requiredKeys: ['correct_deadline', 'image_deadline'], 
      bonusKeys: ['correct_deadline','image_deadline']
    },
    detailResultsView: 'graded',
  }
});

export default (state = defaultState, action) => {
  switch (action.type) {
    case 'UPDATE_LOGIN_STATUS':
      return state.set('login', immutable.fromJS(action.data));
    case 'UPDATE_ACTIVE_EXERCISE':
      return state.set('activeExercise', action.activeExercise);
    case 'UPDATE_EXERCISE_JSON':
      return state.setIn(['exerciseState',action.exercise, 'json'], immutable.fromJS(action.json));
    case 'UPDATE_EXERCISE_STATE':
      return state.mergeDeepIn(['exerciseState', action.exercise], immutable.fromJS(action.state));
    case 'UPDATE_EXERCISES_STATE':
      return state.mergeDeepIn(['exerciseState'], immutable.fromJS(action.state));
    case 'UPDATE_EXERCISES':
      return state.merge({
        'exercises': immutable.fromJS(action.exercises),
        'folder': action.folder
      });
    case 'SET_EXERCISE_TREE':
      return state.set('exerciseTree', immutable.fromJS(action.exercisetree));
    case 'UPDATE_QUESTION_RESPONSE':
      return state.setIn(['exerciseState', action.exercise, 'question', action.question, 'response'], immutable.fromJS(action.response));
      //return state.mergeDeep(action.data);
    case 'UPDATE_EXERCISE_XML':
      return state.setIn(['exerciseState', action.exercise, 'xml'], action.xml);
    case 'UPDATE_EXERCISE_ACTIVE_XML':
      return state.setIn(['exerciseState', action.exercise, 'activeXML'], action.xml);
    case 'SET_SAVE_PENDING':
      return state.setIn(['exerciseState', action.exercise, 'savepending'], action.pending);
    case 'SET_SAVE_ERROR':
      return state.setIn(['exerciseState', action.exercise, 'saveerror'], action.error);
    case 'SET_RESET_PENDING':
      return state.setIn(['exerciseState', action.exercise, 'resetpending'], action.pending);
    case 'SET_EXERCISE_MODIFIED':
      return state.setIn(['exerciseState', action.exercise, 'modified'], action.modified);
    case 'UPDATE_PENDING_STATE':
      return state.mergeDeepIn(['pendingState'], immutable.fromJS(action.pendingstate));
    case 'UPDATE_ACTIVE_ADMIN_TOOL':
      return state.set('activeAdminTool', action.tool);
    case 'SET_IMAGE_ANSWERS':
      return state.setIn(['exerciseState', action.exercise, 'image_answers'], immutable.fromJS(action.imageAnswers));
    case 'SET_IMAGE_ANSWERS_DATA':
      return state.setIn(['exerciseState', action.exercise, 'image_answers_data'], immutable.fromJS(action.imageAnswersData));
    case 'UPDATE_EXERCISE_STATISTICS':
      return state.mergeDeepIn(['exerciseState'], immutable.fromJS(action.stats));
    case 'UPDATE_AGGREGATE_STATISTICS':
      return state.mergeDeepIn(['statistics', 'aggregates'], immutable.fromJS(action.aggregates));
    case 'UPDATE_STUDENT_RESULTS':
      return state.setIn(['results', 'studentResults'], immutable.fromJS(action.results));
    case 'SET_EXERCISE_RECENT_RESULTS':
      return state.setIn(['results', 'exercises', action.exercise, 'recent'], immutable.fromJS(action.data));
    case 'UPDATE_MENU_PATH':
      return state.setIn(['menuPath'], action.path);
    case 'UPDATE_MENU_LEAF_DEFAULTS':
      return state.setIn(['menuLeafDefaults'].concat(action.path), action.value);
    case 'UPDATE_EXERCISES_RELOAD_MESSAGES':
      return state.setIn(['exercisesReloadMessages'], immutable.fromJS(action.messages));
    case 'UPDATE_AUDITS':
      return state.setIn(['audit', 'audits'], action.audits);
    case 'UPDATE_AUDIT':
      return state.mergeIn(['audit', 'audits', action.audit], immutable.fromJS(action.data));
    case 'SET_AUDIT_EXERCISE_STATS':
      return state.setIn(['exerciseState', action.exercise, "auditStats"], immutable.fromJS(action.data));
    case 'SET_ACTIVE_AUDIT':
      return state.setIn(['audit', 'activeAudit'], action.audit);
    case 'SET_ACTIVITY_RANGE':
      return state.setIn(['activityRange'], action.range);
    case 'SET_TABLE_SORT_FIELD':
      return state.setIn(['tables', action.tableId, 'sortField'], action.field);
    case 'SET_TABLE_SORT_REVERSE':
      return state.setIn(['tables', action.tableId, 'sortReverse'], action.reverse);
    case 'SET_RESULTS_FILTER':
      return state.mergeDeepIn(['results', 'filters'], action.filter);
    case 'SET_DETAIL_RESULTS_FILTER':
      return state.mergeIn(['results', 'detailResultsFilters'], action.filter);
    case 'UPDATE_STUDENT_DETAIL_RESULTS':
      return state.setIn(['results', 'detailResults', action.user], immutable.fromJS(action.results));
    case 'SET_SELECTED_STUDENT_RESULTS':
      return state.setIn(['results', 'selectedUser'], action.user);
    case 'SET_DETAIL_RESULT_EXERCISE':
      return state.setIn(['results', 'detailResultExercise'], action.exercise);
    case 'SET_DETAIL_RESULTS_VIEW':
      return state.setIn(['results', 'detailResultsView'], action.view);
    case 'UPDATE_EXERCISE_TREE_UI':
      return state.mergeDeepIn(['exerciseTreeUI'], action.tree);
    default:
      return state
  }
}
