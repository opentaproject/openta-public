import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercises, 
  fetchExerciseXML,
  fetchExerciseTree,
  fetchExercise
} from '../fetchers.js';

import { 
  updateActiveExercise,
  updateMenuPathArray,
} from '../actions.js';
import immutable from 'immutable';
import moment from 'moment';
import Spinner from './Spinner.jsx'
import Badge from './Badge.jsx';
import {SUBPATH} from '../settings.js';

var difficulties = {
  '1': 'Lätt',
  '2': 'Medel',
  '3': 'Svår',
  'none': ''
};

function listClass(item, active) {
  if(item === active)return "uk-active";
  else return "";
}

function generateItem(onClickFunc, exercise, activeExercise, exerciseState, meta, showStatistics) {
  var onExerciseClick = (key, loaded) => {
    UIkit.offcanvas.hide();
    onClickFunc(key, loaded);
  }; 
  var deadlineClass = "uk-badge-primary";
  var legend = 'Obligatorisk';
  if( meta.get('bonus', false) ) {
    deadlineClass = "uk-badge-warning";
    legend = 'Bonus';
  }
  if(showStatistics) {
    var percent = exerciseState.getIn([exercise.get('exercise_key'), 'percent_complete'], 0);
    if(percent === null)percent = 0;
  }
  var imageUploaded = exerciseState.getIn([exercise.get('exercise_key'), 'image_answers'], immutable.List([])).size > 0;
  var imageUploadClass = imageUploaded ? "uk-badge-success" : "uk-badge-danger";
return (
      <li className={exercise.get('exercise_key') === activeExercise ? "uk-active" : ""} key={exercise.get('exercise_key')}>
        <a className={ meta.get('published', false) ? "" : "exercise-unpublished" } onClick={() => onExerciseClick(exercise.get('exercise_key'), exerciseState.getIn([exercise.get('exercise_key'),'json'], immutable.Map({})).isEmpty())}>
          <ul >
            <li>
              <div className="exercise-list-thumb-wrap">
              <img className="uk-margin-right" style={{maxHeight: '40px'}} height="40px" src={SUBPATH + '/exercise/' + exercise.get('exercise_key') + '/asset/thumbnail.png'}/>
              <div className="exercise-thumb-badge">
              { meta.get('difficulty', false) && <Badge className="uk-badge-notification">{difficulties[meta.get('difficulty','none')]}</Badge> }
              { /*meta.get('required', false) && <Badge className="uk-badge-notification"><i className="uk-icon uk-icon-asterisk" title="Obligatorisk"/></Badge> */}
              { /*meta.get('bonus', false) && <Badge className="uk-badge-notification uk-badge-warning"><i className="uk-icon uk-icon-plus uk-text-bold " title="Bonus"/></Badge> */}
              { meta.get('solution', false) && <Badge className={"uk-badge-notification"}>lösning</Badge> }
              { meta.get('deadline_date',false) && <Badge className={"uk-badge-notification uk-text-small " + deadlineClass} title={legend}><i className="uk-icon uk-icon-calendar uk-text-bold uk-margin-small-right"/>{moment(meta.get('deadline_date')).format('D MMM')}</Badge> }
              { meta.get('image', false) && <Badge className={"uk-badge-notification " + imageUploadClass}><i className="uk-icon uk-icon-camera"/></Badge> }
              {exerciseState.getIn([exercise.get('exercise_key'), 'correct'], false) && <span className="uk-badge uk-badge-notification uk-badge-success "><i className="uk-icon uk-icon-check"/></span> }
              </div>
              </div>
            </li>
            <li className="uk-text-break">{exercise.get('name')}</li>
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

const BaseExercises = ({ exerciselist, folder, activeExercise, exerciseState, onExerciseClick, onBack, pendingState, showStatistics }) => (
  <div className="uk-text-center " id="exercises-menu">
    <div id="offcanvas-exercise-list" className="uk-offcanvas">
      <div className="uk-offcanvas-bar">
        <ul className="uk-nav uk-nav-offcanvas">
          <li className="uk-nav-header" key="header">
            <a onClick={(ev) => { UIkit.offcanvas.hide(); onBack() } }><i className="uk-icon uk-icon-arrow-left uk-margin-small-right"></i><span className="uk-text-small">{folder.split('.')[0]}</span></a> 
          </li>
          { exerciselist.map( exercise => generateItem(onExerciseClick, exercise, activeExercise, exerciseState, exercise.get('meta') || immutable.Map({}), showStatistics)) }
        </ul>
      </div>
    </div>
    { /*<a href="#offcanvas-exercise-list" className="uk-navbar-toggle exercise-list-off-canvas" data-uk-offcanvas/> */ }
    <ul className="uk-nav uk-nav-side uk-list-space exercise-menu exercise-list-on-canvas">
    <li className="uk-nav-header" key="header">
      <a onClick={(ev) => onBack()}><i className="uk-icon uk-icon-medium uk-icon-arrow-left"></i></a> <span className="uk-text-large">{folder.split('.')[0]}</span>
    </li>
    { pendingState.get('exerciseList', false) && (<Spinner/>) }
    {exerciselist/*.sort((a,b) => a.get('name').localeCompare(b.get('name')))*/.map( exercise => {
      var meta = exercise.get('meta');
      if(!meta)meta = immutable.Map({});
      var key = exercise.get('exercise_key');
      return generateItem(onExerciseClick, exercise, activeExercise, exerciseState, meta, showStatistics);
      })}
    </ul>
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
  }
  )
};

function handleBack() {
  return dispatch => {
    dispatch(fetchExerciseTree());
    dispatch(updateActiveExercise(""));
    dispatch(updateMenuPathArray([]));
  }
}

const mapDispatchToProps = dispatch => {
  return {
    onExerciseClick: (exercise, empty) => dispatch(fetchExercise(exercise, empty)),
    onBack: () => dispatch(handleBack())
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercises)
