// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React from 'react';
import { env_source , adobe_id } from '../settings';
import PropTypes from 'prop-types';
import { store } from '../store';
import { connect } from 'react-redux';
import ExerciseList from './ExerciseList';
import Exercise from './Exercise';
import StudentExercise from './StudentExercise';
import Header from './Header';
import Course from './Course';
import CourseOptions from './CourseOptions';
import CourseExercisesImport from './CourseExercisesImport';
import CourseImportZip from './CourseImportZip';
import CourseExercisesExport from './CourseExercisesExport';
import EditExerciseOptions from './EditExerciseOptions.jsx';
import CourseExport from './CourseExport';
import CourseDuplicate from './CourseDuplicate';
import ServerImport from './ServerImport';
import ReloadExercises from './ReloadExercises';
import ValidateExercises from './ValidateExercises';
import immutable from 'immutable';
import { menuPositionAt, menuPositionUnder } from '../menu.js';
import { fetchExercise, fetchExerciseRemoteState } from '../fetchers.js';
import PDFAnnotationTools from './PDFAnnotationTools';
// import { Suspense } from 'react';

{
  /* const NowResults = React.lazy(() => import('./Results'));
const NowAuthorExercise = React.lazy(() => import('./AuthorExercise'));
function Results() {
  return (
    <div>
      <Suspense fallback={<div>Loading...</div>}>
        <NowResults />
      </Suspense>
    </div>
  );
}

function AuthorExercise() {
  return (
    <div>
      <Suspense fallback={<div>Loading...</div>}>
        <NowAuthorExercise />
      </Suspense>
    </div>
  );
}

*/
}
import Results from './Results.jsx';
import AuthorExercise from './AuthorExercise';
//const Results = React.lazy( () => import("./Results"))

class BaseApp extends React.Component {
  static propTypes = {
    admin: PropTypes.bool,
    author: PropTypes.bool,
    view: PropTypes.bool,
    activeExercise: PropTypes.string,
    menuPath: PropTypes.object,
    anonymous: PropTypes.bool,
    exerciseKey: PropTypes.string,
    lti_login: PropTypes.bool,
    selected: PropTypes.string
  };

  constructor() {
    super();
    var e = document.getElementById('app');
    //for (let e of els) { console.log("E = ", e.getAttribute('exercisekey') ) }
    //this.exerciseKey= document.getElementsByTagName('div')[0].getAttribute('exercisekey')  || false
    this.exerciseKey = e.getAttribute('exercisekey');
  }

  // https://v320a.localhost:8000/1/single/23a06f95-4d12-4c41-a29a-4936a0651df4/
  // https://v320a.localhost:8000/1/single/fef2fb2a-e4f4-4cb2-9aff-ffaf88a1c3d3/

  //UNSAFE_componentWillMount(props, state, root) {
  //    console.log("APP WILL MOUNT")
  //    try {
  //      this.exerciseKey= document.getElementsByTagName('div')[0].getAttribute('exercisekey')  || false
  //     } catch (error) {
  //      this.exerciseKey = false
  //   }
  //
  //    console.log("this.exerciseKey in MOUNT", this.exerciseKey)
  //var doc = document.getElementsByTagName('div')[1]
  //console.log("PRINT this.exerciseKey", doc.getAttribute('exercisekey'))
  //console.log("PRINT this.exerciseKey", this.exerciseKey)
  //if ( this.props.user_pk && this.props.activeCourse ){
  //   fetchUserExercises(this.props.activeCourse,this.props.user_pk)
  //   }
  //this.compact = this.props.compact  ? true : false
  //if (this.props.onExerciseClick ){
  //   this.onExerciseClick = this.props.onExerciseClick
  //   } else {
  //  this.onExerciseClick = this.props.onDefaultExerciseClick
  //  }
  // this.onExerciseClick = this.props.onDefaultExerciseClick

  // }

  //onDefaultExerciseClick: (exercise, folder) => {
  //  dispatch(updatePendingStateIn(["exerciseList"], true));
  //  dispatch(fetchExerciseRemoteState(exercise))
  //    .then(dispatch(fetchExercise(exercise, true)))
  //    .then(dispatch(navigateMenuArray(["activeExercise"])));
  //  dispatch(updateExercises([], folder));
  //  dispatch(fetchSameFolder(exercise, folder));
  //},

  // https://v320a.localhost:8000/1/single/23a06f95-4d12-4c41-a29a-4936a0651df4
  // https://v320a.localhost:8000/1/single/fef2fb2a-e4f4-4cb2-9aff-ffaf88a1c3d3/
  render() {
    //console.log("App.jsx this.exerciseKey = ", this.exerciseKey)
    var single = false;
    if (!('None' == this.exerciseKey)) {
      var single = true;
      var exercise = this.exerciseKey;
      var exerciseKey = exercise;
    }
    //var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));

    // https://v320a.localhost:8000/exercise/23a06f95-4d12-4c41-a29a-4936a0651df4
    // console.log("SINGLE = ", single )
    // SINGLE TRIGGERED IF THERE IS A SINGLE EXERCISE TO BE SHOWN ON FOR INSTANCE A WEBPATH
    // THIS HAS NOT BEEN SERIOUSLY IMPLEMENTED
    if (single) {
      store.dispatch(fetchExerciseRemoteState(exercise)).then(store.dispatch(fetchExercise(exercise, true)));
      return (
        <div id="content" className="uk-width-1-1  ">
          	<div id="main" className="uk-grid ">
        		<div className="myheader uk-width-1-1"> <Header anonymous={anonymous} lti_login={this.props.lti_login} show_edit_toggle={show_edit_toggle} show_home={show_home} /> </div>
        		<div id="content" className=" uk-container-center uk-flex uk-flex-center  uk-width-1-1  "> <div className="exercise "> <Exercise exerciseKey={exercise} /> </div> </div>
	       </div>

	  </div> 
      );
    }
    //console.log("NOT SINGLE")

    var show_home = menuPositionUnder(this.props.menuPath, ['activeExercise']);
    var show_edit_toggle = !menuPositionUnder(this.props.menuPath, ['results']);
    var anonymous = this.props.anonymous;

    //console.log('ENV_SOURCE = ', env_source);
    return (
      <div className="uk-grid ">
        <div className="myheader uk-width-1-1">
          <Header
            anonymous={anonymous}
            lti_login={this.props.lti_login}
            show_edit_toggle={show_edit_toggle}
            show_home={show_home}
          />
        </div>
        <div id="content" className="uk-width-1-1  ">
          <div id="main" className="uk-grid ">
            <div className="uk-container-center uk-flex uk-flex-center uk-width-1-1">
              {/*this.props.activeExercise === "" && <div className="uk-width-medium-1-6"/>*/}
              {(menuPositionUnder(this.props.menuPath, ['exercises', 'activity']) ||
                menuPositionAt(this.props.menuPath, ['exercises']) ||
                menuPositionAt(this.props.menuPath, [])) && (
                <div className="uk-width-medium-4-5">
                  <Course key={this.props.selected} />
                </div>
              )}
              {menuPositionUnder(this.props.menuPath, ['results']) && (
                <div className="uk-width-1-1 uk-margin-small-left results">
                  <Results />
                </div>
              )}
              {menuPositionUnder(this.props.menuPath, ['course', 'options']) && (
                <div className="uk-width-1-1 uk-margin-small-left">
                  <CourseOptions />
                </div>
              )}
              {/*menuPositionUnder(this.props.menuPath, ['course', 'import_zip']) && (
                <div className="uk-width-1-1 uk-margin-small-left">
                  <CourseImportZip />
                </div>
              )*/}
              {menuPositionUnder(this.props.menuPath, ['course', 'import_zip']) && (
                <div className="uk-width-1-1 uk-margin-small-left">
                  <CourseExercisesImport />
                </div>
              )}
              {menuPositionUnder(this.props.menuPath, ['course', 'export_exercises']) && (
                <div className="uk-width-1-1 uk-margin-small-left">
                  <CourseExercisesExport />
                </div>
              )}
              {menuPositionUnder(this.props.menuPath, ['server', 'export']) && (
                <div className="uk-width-1-1 uk-margin-small-left">
                  <CourseExport />
                </div>
              )}
              {menuPositionUnder(this.props.menuPath, ['course', 'duplicate']) && (
                <div className="uk-width-1-1 uk-margin-small-left">
                  <CourseDuplicate action="duplicate" />
                </div>
              )}
              {menuPositionUnder(this.props.menuPath, ['course', 'modify']) && (
                <div className="uk-width-1-1 uk-margin-small-left">
                  <CourseDuplicate action="modify" />
                </div>
              )}
              {menuPositionUnder(this.props.menuPath, ['server', 'import']) && (
                <div className="uk-width-1-1 uk-margin-small-left">
                  <ServerImport />
                </div>
              )}
              {menuPositionAt(this.props.menuPath, ['exercises', 'reload'])  && (
                <div className="uk-width-medium-2-3 uk-margin-small-left">
                  <ReloadExercises />
                </div>
              )}

	      {menuPositionAt(this.props.menuPath, ['exercises', 'validate']) && (
                <div className="uk-width-medium-2-3 uk-margin-small-left">
                  <ValidateExercises />
                </div>
              )}


              {menuPositionAt(this.props.menuPath, ['exercises', 'exercise_options']) && (
                <div className="uk-width-medium-2-3 uk-margin-small-left">
                  <EditExerciseOptions />
                </div>
              )}
              {/*(this.props.admin || this.props.author) ? <span/> : <div className="exercise-spacing"></div> */}
              {menuPositionUnder(this.props.menuPath, ['activeExercise']) && (
                <div>
                  <ExerciseList showOnCanvas={false} />
                </div>
              )}
              {menuPositionUnder(this.props.menuPath, ['activeExercise']) &&
                ((this.props.author || this.props.admin || this.props.view) &&
                !menuPositionUnder(this.props.menuPath, ['activeExercise', 'student']) ? (
                  <AuthorExercise />
                ) : (
                  <div className="exercise ">
                    <StudentExercise />
                  </div>
                ))}
            </div>
          </div>
        </div>
        {/*<div className='  footer'> <Footer /> </div> */}
      </div>
    );
  }
}

const mapStateToProps = (state) => ({
  selected: state.getIn(['selectedExercises'], immutable.List([])).length > 0 ? 'selected_yes' : 'selected_no',
  admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
  author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
  view: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
  student: state.getIn(['login', 'groups'], immutable.List([])).includes('Student'),
  activeExercise: state.get('activeExercise'),
  menuPath: state.get('menuPath'),
  compactview: state.getIn(['login', 'compactview'], true),
  anonymous: state.getIn(['login', 'groups'], immutable.List([])).includes('AnonymousStudent'),
  lti_login: state.getIn(['login', 'lti_login'], true),
  course_name: state.getIn(['course', 'course_name']),
  username: state.getIn(['login', 'username'])
});

export default connect(mapStateToProps)(BaseApp);
