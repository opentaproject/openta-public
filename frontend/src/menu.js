import immutable from 'immutable';
import { use_chatgpt } from './settings.js'
import {
  updateMenuLeafDefaults,
  updateMenuPath,
  setActivityRange,
  setActiveAudit,
  setDetailResultExercise
} from './actions.js';
import {
  fetchStudentResults,
  fetchExerciseStatistics,
  reloadExercises,
  validateExercises,
  fetchCurrentAuditsExercise,
  fetchExerciseRecentResults,
} from './fetchers.js';

var menutree = {
  menuItems: {
    server: {
      name: 'Server',
      key: 'server',
      reqGroup: ['SuperUser'],
      menuItems: {
        import: {
          name: 'Import',
          key: 'import'
        },

        export: {
          name: 'Export',
          key: 'export'
        }
      }
    },
    course: {
      name: 'Course',
      key: 'course',
      reqGroup: ['SuperUser'],
      menuItems: {
        options: {
          name: 'Options',
          key: 'options'
        },
        import_zip: {
          name: 'Import exercises',
          key: 'import_zip',
          reqGroup: ['SuperUser']
        },
        export_exercises: {
          name: 'Export exercises',
          key: 'export_exercises',
          reqGroup: ['SuperUser']
        },
        duplicate: {
          name: 'Duplicate',
          key: 'duplicate',
          reqGroup: ['SuperUser']
        },
        modify: {
          name: 'Modify',
          key: 'modify',
          reqGroup: ['SuperUser']
        }
      }
    },
    exercises: {
      name: 'Exercises',
      key: 'exercises',
      reqGroup: ['Admin', 'View', 'SuperUser'],

      menuItems: {

        validate: {
          name: 'Validate exercises',
          key: 'validate',
          onLoad: validateExercises(false, null),
          reqGroup: ['SuperUser']
        },


        reload: {
          name: 'Reload exercises',
          key: 'reload',
          onLoad: reloadExercises(false, null),
          reqGroup: ['SuperUser']
        },




        exercise_options: {
          name: 'Exercise Options',
          key: 'exercise_options',
          reqGroup: ['Admin', 'SuperUser']
        },

        activity: {
          name: 'Activity',
          key: 'activity',
          reqGroup: ['View', 'Admin', 'SuperUser'],
          rememberChoice: true,
          menuItems: {
            hour: {
              name: 'hour',
              key: 'hour',
              onLoad: setActivityRange('1h'),
              reqGroup: ['Author', 'View', 'Admin', 'SuperUser']
            },
            day: {
              name: 'day',
              key: 'day',
              onLoad: setActivityRange('24h'),
              reqGroup: ['Author', 'View', 'Admin', 'SuperUser']
            },
            week: {
              name: 'week',
              key: 'week',
              onLoad: setActivityRange('1w'),
              reqGroup: ['Author', 'View', 'Admin', 'SuperUser']
            },
            all: {
              name: 'all',
              key: 'all',
              onLoad: setActivityRange('all'),
              reqGroup: ['Author', 'View', 'Admin', 'SuperUser']
            }
          }
        }
      }
    },
    results: {
      name: 'Results',
      key: 'results',
      onLoad: fetchStudentResults(),
      reqGroup: ['Admin', 'View', 'SuperUser'],
      rememberChoice: true,
      menuItems: {
        list: {
          name: 'List',
          key: 'list',
          onLoad: setDetailResultExercise(false)
          //menuItems: {
          //  audit: {
          //    invisible: true,
          //    name: 'Audit',
          //    key: 'audit',
          //  }
          //},
        },
        histogram: {
          name: 'Histogram',
          key: 'histogram'
        },
        histogram2: {
          name: 'Histogram2',
          key: 'histogram2'
        },

        histogram3: {
          name: 'Scatterplot 1',
          key: 'histogram3'
        },
        histogramall: {
          name: 'Histogram All',
          key: 'histogramall'
          //onLoad: fetchCourseStatistics(1),
        },
        download: {
          reqGroup: ['Admin', 'SuperUser'],
          name: 'Download',
          key: 'download'
        },
        gradebook: {
          reqGroup: ['Admin', 'SuperUser'],
          name: 'Canvas gradebook',
          key: 'gradebook'
        },
        custom: {
          reqGroup: ['Admin', 'SuperUser'],
          name: 'Custom',
          key: 'custom'
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
        student: {
          name: 'Exercise',
          key: 'student',
          reqGroup: ['Author', 'View', 'Admin', 'SuperUser']
        },
        xmlEditor: {
          name: 'XML & Assets',
          key: 'xmlEditor',
          reqGroup: ['Author', 'SuperUser']
        },
        xmlEditorSplit: {
          name: 'Live edit',
          key: 'xmlEditorSplit',
          reqGroup: ['View', 'Author', 'SuperUser']
        },
        options: {
          name: 'Options',
          key: 'options',
          reqGroup: ['Admin', 'SuperUser']
        },
        statistics: {
          name: 'Statistics',
          key: 'statistics',
          reqGroup: ['View', 'Admin', 'SuperUser', 'Author'],
          onLoad: fetchExerciseStatistics()
        },
        recent: {
          name: 'Recent',
          key: 'recent',
          reqGroup: ['View', 'Admin', 'SuperUser', 'Author'],
          onLoad: fetchExerciseRecentResults()
        },

        regrade: {
          name: 'Regrade',
          key: 'regrade',
          reqGroup: ['Admin', 'SuperUser']
        },




        audit: {
          name: 'Audit',
          key: 'audit',
          reqGroup: ['Admin', 'SuperUser'],
          onLoad: fetchCurrentAuditsExercise(),
          rememberChoice: true,
          menuItems: {
            overview: {
              name: 'Overview',
              key: 'overview',
              reqGroup: ['Admin', 'SuperUser']
            },
            myaudits: {
              name: 'My audits',
              key: 'myaudits',
              onLoad: setActiveAudit(''),
              reqGroup: ['Admin', 'SuperUser']
            },

          }
        }
      }
    }
  }
};
if( use_chatgpt == 'True'  ){
menutree.menuItems.activeExercise.menuItems.analyze = {
          name: 'Analyze',
         key: 'analyze',
        reqGroup: ['Admin', 'SuperUser']
        }
}
var menuTree = immutable.fromJS( menutree )

function traverse(menuPath) {
  var fullPath = immutable.List([]);
  if (menuPath.size > 0) {
    fullPath = menuPath
      .pop()
      .reduce((acc, next) => acc.push(next).push('menuItems'), immutable.List([]))
      .push(menuPath.last())
      .insert(0, 'menuItems');
  }
  return menuTree.getIn(fullPath);
}

function navigateMenuArray(pathArray) {
  return (dispatch, getState) => {
    var path = immutable.fromJS(pathArray);
    var menuItem = traverse(path);
    var state = getState();
    var defaultLeaf = state.getIn(['menuLeafDefaults'].concat(pathArray).concat(['leafDefault']), undefined);
    if (menuItem.has('onLoad')) {
      if (immutable.Iterable.isIterable(menuItem.get('onLoad'))) {
        dispatch(menuItem.get('onLoad').toJS());
      } else {
        dispatch(menuItem.get('onLoad'));
      }
    }
    if (!menuItem.has('menuItems')) {
      dispatch(updateMenuLeafDefaults(path.butLast().toJS(), path.last()));
    }
    if (defaultLeaf && menuItem.get('rememberChoice')) {
      dispatch(navigateMenuArray(path.push(defaultLeaf)));
      //dispatch(updateMenuPath(path.push(defaultLeaf)))
    } else {
      dispatch(updateMenuPath(path));
    }
  };
}

function navigateAgain() {
  return (dispatch, getState) => {
    var state = getState();
    return dispatch(navigateMenuArray(state.get('menuPath').toArray()));
  };
}

function menuPositionUnder(menuPath, pathArray) {
  return menuPath.take(pathArray.length).equals(immutable.List(pathArray));
}
function menuPositionAt(menuPath, pathArray) {
  return menuPath.equals(immutable.List(pathArray));
}

export { traverse, navigateMenuArray, navigateAgain, menuPositionUnder, menuPositionAt };
