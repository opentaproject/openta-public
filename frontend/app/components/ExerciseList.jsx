import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import {
  fetchExercises,
  fetchExerciseXML,
  fetchExerciseTree,
  fetchExercise,
  fetchExerciseRemoteState,
} from '../fetchers.js';

import {
  updateActiveExercise,
  updateMenuPathArray,
} from '../actions.js';
import { navigateMenuArray, navigateAgain } from '../menu.js';
import immutable from 'immutable';
import moment from 'moment';
import Spinner from './Spinner.jsx'
import Badge from './Badge.jsx';
import SafeImg from './SafeImg.jsx';
import T from './Translation.jsx';
import t from '../translations.js'
import {SUBPATH} from '../settings.js';

function listClass(item, active) {
  if(item === active)return "uk-active";
  else return "";
}

function generateItem(onClickFunc,  exercise, activeExercise, exerciseState, meta, showStatistics) {
  var onExerciseClick = (key, loaded) => {
    UIkit.offcanvas.hide();
    onClickFunc(key, loaded);
  };
  var deadlineClass = "uk-badge-primary";
  var dolegend = false
  var legend = ''
  if( meta.get('bonus', false) ) {
    deadlineClass = "uk-badge-warning";
    legend = 'Bonus';
    dolegend = true
  }

  if( meta.get('obligatorisk', false) ) {
    deadlineClass = "uk-badge-primary";
    legend = 'Obligatorisk';
    dolegend = true
  }
  if( meta.get('deadline_date')){
      var duedate =moment(meta.get('deadline_date')).format('D MMM') 
      } else {
      var duedate =  legend
    }
  if(showStatistics) {
    var percent = exerciseState.getIn([exercise.get('exercise_key'), 'percent_complete'], 0);
    if(percent === null)percent = 0;
  }
  var imageUploaded = exerciseState.getIn([exercise.get('exercise_key'), 'image_answers'], immutable.List([])).size > 0;
  var imageUploadClass = imageUploaded ? "uk-badge-success" : "uk-badge-danger";
  var nameDict = exercise.get('translated_name');
  var showcheck  = exerciseState.getIn([exercise.get('exercise_key'), 'tried_all'], false)
return (
      <li className={exercise.get('exercise_key') === activeExercise ? "uk-active" : ""} key={exercise.get('exercise_key')}>
        <a className={ meta.get('published', false) ? "" : "exercise-unpublished" } onClick={() => onExerciseClick(exercise.get('exercise_key'), exerciseState.getIn([exercise.get('exercise_key'),'json'], immutable.Map({})).isEmpty())}>
          <ul >
            <li>
              <div className="exercise-list-thumb-wrap">
              <div className="exercise-thumb-badge">
                { meta.get('difficulty', false) &&
                  <Badge className="uk-badge-notification">{t( meta.get('difficulty','none'))}</Badge> }
              { /*meta.get('required', false) && <Badge className="uk-badge-notification"><i className="uk-icon uk-icon-asterisk" title="Obligatorisk"/></Badge> */}
              { /*meta.get('bonus', false) && <Badge className="uk-badge-notification uk-badge-warning"><i className="uk-icon uk-icon-plus uk-text-bold " title="Bonus"/></Badge> */}
                { meta.get('solution', false) &&
                  <Badge className={"uk-badge-notification"}>lösning</Badge> }
                { dolegend  &&
                  <Badge className={"uk-badge-notification uk-text-small " + deadlineClass} title={legend}>
                    {duedate} 
                  </Badge> }
                { meta.get('image', false) &&
                  <Badge className={"uk-badge-notification " + imageUploadClass}>
                    <i className="uk-icon uk-icon-camera"/>
                  </Badge> }
                { ( ! meta.get('feedback',true) ) &&
                  exerciseState.getIn([exercise.get('exercise_key'), 'tried_all'], false) &&
                  <span className="uk-badge uk-badge-notification uk-badge-warning">
                    <i className="uk-icon uk-icon-check"/></span> }
                { showcheck && ( meta.get('feedback',true) ) &&
                  exerciseState.getIn([exercise.get('exercise_key'), 'correct'], false) &&
                  <span className="uk-badge uk-badge-notification uk-badge-success">
                    <i className="uk-icon uk-icon-check"/></span> }
                { exerciseState.getIn([exercise.get('exercise_key'), 'modified']) &&
                  <Badge className={"uk-badge-notification uk-badge-danger"}>
                    <i className="uk-icon uk-icon-save"/></Badge>}
                { exerciseState.getIn([exercise.get('exercise_key'), 'audit', 'published'], false) &&
                  <Badge type={exerciseState.getIn([exercise.get('exercise_key'), 'audit', 'revision_needed'], false) ? 'error' : 'success'} className={"uk-badge-notification"}>
                    <T>Reviewed</T>
                  </Badge> }
                { !meta.get('published') &&
                  <Badge type='error' className={"uk-badge-notification"}>
                    <T>Unpublished</T></Badge> }
              </div>
              <SafeImg className=""
                       style={{maxHeight: '40px', height:'40px'}}
                       src={SUBPATH + '/exercise/' + exercise.get('exercise_key') + '/asset/thumbnail.png'}>
              </SafeImg>
              </div>
            </li>
            <li className="uk-text-break">
              <T dict={nameDict}>{exercise.get('name')}</T>
            </li>
            { showStatistics &&
              <li>
              <div className="uk-progress uk-margin-remove uk-progress-small uk-progress-success">
                <div className="uk-progress-bar" style={{'width': (percent*100) + '%'}}></div>
              </div>
              </li>
            }
          </ul>
        </a>
      </li>
);
}

const BaseExercises = ({ exerciselist, folder, activeExercise, exerciseState, onExerciseClick,
    onBack, pendingState, showStatistics, showOnCanvas, coursePk }) => (
  <div className="uk-text-center " id="exercises-menu">
    <div id="offcanvas-exercise-list" className="uk-offcanvas">
      <div className="uk-offcanvas-bar">
        <ul className="uk-nav uk-nav-offcanvas">
          <li className="uk-nav-header" key="header">
            <a className='onBackToCourse' onClick={(ev) => { UIkit.offcanvas.hide(); onBack(coursePk) } }>
              <i className="uk-icon uk-icon-arrow-left uk-margin-small-right"></i>
              <span className="uk-text-small">{folder.split('.')[0]}</span>
            </a>
          </li>
          { exerciselist.map( exercise =>
              generateItem(onExerciseClick, exercise, activeExercise, exerciseState, exercise.get('meta') || immutable.Map({}), showStatistics)) }
        </ul>
      </div>
    </div>
    { showOnCanvas &&
    <ul className="uk-nav uk-nav-side uk-list-space exercise-menu exercise-list-on-canvas">
    <li className="uk-nav-header" key="header">
      <a  onClick={(ev) => onBack(coursePk)}><i className="uk-icon uk-icon-medium uk-icon-arrow-left"></i></a> <span className="uk-text-large">{folder.split('.')[0]}</span>
    </li>
    { pendingState.get('exerciseList', false) && (<Spinner/>) }
    {exerciselist.map( exercise => {
      var meta = exercise.get('meta');
      if(!meta)meta = immutable.Map({});
      var key = exercise.get('exercise_key');
      return generateItem(onExerciseClick, exercise, activeExercise, exerciseState, meta, showStatistics);
      })}
    </ul>
    }
  </div>
);

BaseExercises.propTypes = {
  exerciselist: PropTypes.object.isRequired,
  folder: PropTypes.string,
  activeExercise: PropTypes.string,
  exerciseState: PropTypes.object,
  pendingState: PropTypes.object,
  onExerciseClick: PropTypes.func.isRequired,
  onBack: PropTypes.func,
  showOnCanvas: PropTypes.bool,
};

const mapStateToProps = state => {
  var exerciseState = state.getIn(['exerciseState'], immutable.Map({}));
  return (
  {
    exerciselist: state.get('exercises', immutable.List([])),
    folder: state.get('folder', ""),
    activeExercise: state.get('activeExercise') ,
    exerciseState: exerciseState,
    pendingState: state.get('pendingState'),
    showStatistics: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
    coursePk: state.getIn(['activeCourse']),
  }
  )
};

function handleBack(coursePk) {
  return dispatch => {
    dispatch(fetchExerciseTree(coursePk));
    dispatch(updateActiveExercise(""));
    dispatch(navigateMenuArray([]));
  }
}

const mapDispatchToProps = dispatch => {
  return {
    onExerciseClick: (exercise, empty) =>  {
      dispatch(fetchExercise(exercise, empty))
      dispatch(fetchExerciseRemoteState(exercise))
      dispatch(navigateAgain());
    },
    onBack: (coursePk) => dispatch(handleBack(coursePk))
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercises)
