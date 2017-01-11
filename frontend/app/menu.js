import immutable from 'immutable';
import { 
  updateMenuLeafDefaults,
  updateMenuPath,
  setActivityRange,
  setDetailResultExercise,
} from './actions.js';
import {
  fetchStudentResults,
  fetchExerciseStatistics,
  reloadExercises,
  fetchUnsentAudits,
} from './fetchers.js';

var menuTree = immutable.fromJS({
  menuItems: {
    exercises: {
      name: 'Exercises',
      key: 'exercises',
      reqGroup: [],
      menuItems: {
        reload: {
          name: 'Reload exercises',
          key: 'reload',
          onLoad: reloadExercises(),
          reqGroup: 'Author',
        },
        activity: {
          name: 'Activity',
          key: 'activity',
          rememberChoice: true,
          menuItems: {
            hour: {
              name: 'hour',
              key: 'hour',
              onLoad: setActivityRange('1h'),
              reqGroup: 'View',
            },
            day: {
              name: 'day',
              key: 'day',
              onLoad: setActivityRange('24h'),
              reqGroup: 'View',
            },
            week: {
              name: 'week',
              key: 'week',
              onLoad: setActivityRange('1w'),
              reqGroup: 'View',
            },
            all: {
              name: 'all',
              key: 'all',
              onLoad: setActivityRange('all'),
              reqGroup: 'View',
            },
          },
        },
      },
    },
    results: {
      name: 'Results',
      key: 'results',
      onLoad: fetchStudentResults(),
      reqGroup: [],
      rememberChoice: true,
      menuItems: {
        list: {
          name: 'List',
          key: 'list',
          onLoad: setDetailResultExercise(false),
        },
        histogram: {
          name: 'Histogram',
          key: 'histogram'
        },
        histogram2d: {
          name: 'Histogram 2d',
          key: 'histogram2d'
        },
        download: {
          name: 'Download',
          key: 'download',
        }
      }
    },
    activeExercise: {
      invisible: true,
      name: 'Exercise',
      key: 'activeExercise',
      reqGroup: [],
      rememberChoice: true,
      menuItems: {
        xmlEditor: {
          name: 'XML Editor',
          key: 'xmlEditor',
          reqGroup: 'Author'
        },
        options: {
          name: 'Options',
          key: 'options',
          reqGroup: 'Admin'
        },
        statistics: {
          name: 'Statistics',
          key: 'statistics',
          reqGroup: 'View',
          onLoad: fetchExerciseStatistics(),
        },
        /*audit: {
          name: 'Audit',
          key: 'audit',
          reqGroup: 'Admin',
          onLoad: fetchUnsentAudits(),
        }*/
      }
    }
  }
});

function traverse(menuPath) {
  var fullPath = immutable.List([])
  if(menuPath.size > 0) {
    fullPath = menuPath.pop().reduce(
    (acc, next) => acc.push(next).push('menuItems'), immutable.List([])
  ).push(menuPath.last()).insert(0, 'menuItems');
  }
  return menuTree.getIn(fullPath)
}

function navigateMenuArray(pathArray) {
  return (dispatch, getState) => {
    var path = immutable.fromJS(pathArray);
    var menuItem = traverse(path);
    var state = getState();
    var defaultLeaf = state.getIn(['menuLeafDefaults'].concat(pathArray).concat(['leafDefault']), undefined)
    if(menuItem.has('onLoad')){
      if(immutable.Iterable.isIterable(menuItem.get('onLoad')))
        dispatch(menuItem.get('onLoad').toJS())
      else
        dispatch(menuItem.get('onLoad'))
    }
    if(!menuItem.has('menuItems'))
      dispatch(updateMenuLeafDefaults(path.butLast().toJS(), path.last()))
    if(defaultLeaf && menuItem.get('rememberChoice')) {
      dispatch(navigateMenuArray(path.push(defaultLeaf)))
      //dispatch(updateMenuPath(path.push(defaultLeaf)))
    }
    else
      dispatch(updateMenuPath(path))
  }
}

function navigateAgain() {
  return (dispatch, getState) => {
    var state = getState();
    return dispatch(navigateMenuArray(state.get('menuPath').toArray()));
  }
}

function menuPositionUnder(menuPath, pathArray) {
  return menuPath.take(pathArray.length).equals(immutable.List(pathArray));
}
function menuPositionAt(menuPath, pathArray) {
  return menuPath.equals(immutable.List(pathArray));
}

export { traverse, navigateMenuArray, navigateAgain, menuPositionUnder, menuPositionAt }
