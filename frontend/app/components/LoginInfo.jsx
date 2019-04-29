import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import {
  fetchExercises,
  fetchExerciseXML,
  fetchExerciseJSON,
  fetchExercise,
  fetchSameFolder,
  saveExercise,
  resetExercise,
} from '../fetchers.js';

import {
  updateActiveAdminTool,
  updateActiveExercise,
  setSavePendingState,
  setResetPendingState,
  updatePendingStateIn,
  setExerciseModifiedState,
} from '../actions.js';
import {
  navigateMenuArray
} from '../menu.js';

import immutable from 'immutable';
import _ from 'lodash';
import {SUBPATH} from '../settings.js';
import Spinner from './Spinner.jsx';
import Menu from './Menu.jsx';
import ExerciseHistory from './ExerciseHistory.jsx';
import DeleteExercise from './DeleteExercise.jsx';
import LanguageSelect from './LanguageSelect.jsx';
import CourseSelect from './CourseSelect.jsx';
import { throttleParseXML } from './AuthorExercise.jsx';
import { menuPositionAt, menuPositionUnder } from '../menu.js';

var groupIcons = {
  'Admin': {
    icon: "uk-icon-user-md",
    alt: "Administrator"
  },
  'Author': {
    icon: "uk-icon-pencil",
    alt: "Author"
  },
  'Student': {
    icon: "uk-icon-graduation-cap",
    alt: "Student"
  }
}

var pendingPaths = [
  {
    path: ['exercises_statistics'],
    name: ''
  },
];



var Tools = ({showsave, onsave, savepending, savesuccess, saveerror, showreset, resetpending, onreset}) => {
    return(
    
    <div className="uk-button-group">
        { showsave && <a className={"uk-button uk-button-small " + (saveerror ? "uk-button-danger" : "uk-button-success")} onClick={onsave}>Save {savepending ? (<i className="uk-icon-cog uk-icon-spin"></i>) : (<i className="uk-icon-floppy-o"></i>)} </a> }
        { showreset && savepending !== true && <a className="uk-button uk-button-small uk-button-primary" title="Reset to last saved version." data-uk-tooltip onClick={onreset}> {resetpending ? (<i className="uk-icon-cog uk-icon-spin"></i>) : (<i className="uk-icon-undo"></i>)}</a> }
      <ExerciseHistory/> 
      <DeleteExercise/>
    </div>
)};

const BaseLoginInfo = ({ username, groups, course, admin, author, viewer, activeExercise,
      exerciseState, activeAdminTool, onXMLEditorClick, onOptionsClick, onStatisticsClick, onSave,
      onReset, onHome, pendingState, menuPath, motd,languages,lti_login,compactview}) => {
    var savePending = exerciseState.get('savepending');
    var saveError = exerciseState.get('saveerror');
    var resetPending = exerciseState.get('resetpending');
    var modified = exerciseState.get('modified');
    var no_xml_error = exerciseState.get('xmlError') == null;
    var can_save = modified && no_xml_error;
    var savereset = (
      <Tools showsave={can_save} savepending={savePending} savesuccess={!modified && saveError === false} showreset={modified} saveerror={saveError} resetpending={resetPending} onsave={(event) => onSave(activeExercise)} onreset={(event) => onReset(activeExercise) }  />
    );

  var renderGroupIcons = groups.map( group => {
                                    if(group in groupIcons)
                                      return (<i key={group} className={"uk-icon uk-text-success uk-margin-small-left " + groupIcons[group].icon} title={groupIcons[group].alt}/>)
                                    else
                                      return (<span key={group}/>)
  });
  console.log("COMPACT_VIEW = ", compactview )
  console.log("LTI_LOGIN = ", lti_login)
  var renderPending = pendingPaths.map( item => {
    return (pendingState.getIn(item.path, false) && (<span key={item.path}>{item.name}<Spinner icon="uk-icon-bar-chart" size="" className="uk-margin-small-left"/></span>))
  });
var studentViewDOM = (author || viewer) ? (<button onClick={(e) => UIkit.modal.confirm("View site as student?", () => window.open(SUBPATH + "/hijack/username/student" , "_self"))} className="uk-button uk-button-mini uk-alert-warning" data-uk-tooltip title="Log in as default student">Student view</button>) : '';
var authorview = compactview ? 'Full Site' : 'View Only'
var compactViewDOM = (author || viewer) ? (<button onClick={(e) => UIkit.modal.confirm(authorview, () => window.open(SUBPATH + "/view_toggle/" , "_self"))} className="uk-button uk-button-mini uk-alert-warning" data-uk-tooltip title="Log in as default student">{authorview} </button>) : '';

var canViewXML = author || viewer || admin
return (
  <nav id="login" className="uk-nav uk-navbar-attached ta-nav border-bottom">
  <div className="uk-container uk-container-center">
  <div className="uk-navbar-content uk-flex uk-flex-wrap">
  { activeExercise && menuPositionUnder(menuPath, ['activeExercise']) &&
  <div className="uk-navbar-content uk-padding-remove">
    <a href="#offcanvas-exercise-list" className="uk-navbar-toggle exercise-list-off-canvas uk-padding-remove" data-uk-offcanvas/>
  </div> }
  <ul className="uk-navbar-nav exercise-list-on-canvas"><li>
  <a className="uk-navbar-brand" onClick={onHome}>
    <i className="uk-icon uk-icon-medium uk-icon-circle-o"></i>
  </a>
  </li></ul>
  <div className="uk-vertical-align">
  <span className="uk-vertical-align-middle">
    {renderGroupIcons}
    <span className="uk-text-middle">{username}</span>
    { admin && <span className="uk-text-small uk-text-middle"> (admin)</span> }
    <span className="uk-text-middle uk-text-warning"> {motd} </span> 
  </span>
  </div>
  </div>
  <div className="uk-navbar-flip">
  {   author && activeExercise && ( menuPositionUnder(menuPath, ['activeExercise', 'xmlEditor']) || menuPositionUnder(menuPath, ['activeExercise', 'xmlEditorSplit']) ) &&
  <div className="uk-navbar-content">
  </div>
  }
  <ul className="uk-navbar-nav">
<li>
        <div className="uk-navbar-content">
        {compactViewDOM}
      </div>
    </li>


    { ! compactview && (
    <li>
      <div className="uk-navbar-content">
        {studentViewDOM}
      </div>
    </li>
    ) }
    <li>
      <div className="uk-navbar-content">
      <LanguageSelect/>
      </div>
    </li>
    { ! compactview && (
    <li>
      <div className="uk-navbar-content">
      <CourseSelect/>
      </div>
    </li>
    )
    }
    { ! compactview && 
     ( <li>
        <a href={"mailto:" + course.toLowerCase() + "@openta.se"} className="uk-padding-remove" data-uk-tooltip title={"Skicka ett mail till " + course.toLowerCase() + "@openta.se"}><span className="uk-text-primary">Problem?</span></a>
      </li>
    )}
{ lti_login && (
<li>
<a title="Change password" href={SUBPATH + "/change_password/?next=" }><i className="uk-icon uk-icon-lock uk-text-large uk-text-middle"></i></a>
</li>
    ) }
{ lti_login && (
<li>
<a title="Edit profile" href={SUBPATH + "/edit_profile/?next=" }><i className="uk-icon uk-icon-user uk-text-large uk-text-middle"></i></a>

</li>
    ) }

      <li >
      <a title="Logga ut" href={SUBPATH + "/logout"}><i className="uk-icon uk-icon-sign-out uk-text-large uk-text-middle"></i></a>
      </li>
    


  </ul>
  </div>
  <div className="uk-navbar-content uk-margin-small-top uk-flex uk-flex-middle uk-flex-wrap" style={{height: 'auto'}}>
  { renderPending }
  { ! compactview &&  canViewXML && <Menu/> }
</div>
  </div>
  </nav>
);
}

BaseLoginInfo.propTypes = {
  username: PropTypes.string,
  admin: PropTypes.bool,
  author: PropTypes.bool,
  groups: PropTypes.object,
  course: PropTypes.string,
  activeExercise: PropTypes.string,
  exerciseState: PropTypes.object,
  activeAdminTool: PropTypes.string,
  onXMLEditorClick: PropTypes.func,
  onOptionsClick: PropTypes.func,
  onStatisticsClick: PropTypes.func,
  onHome: PropTypes.func,
  pendingState: PropTypes.object,
  menuPath: PropTypes.object,
  compactview: PropTypes.bool,

};

function handleSave(exercise) {
  return (dispatch, getState) => {
    var state = getState();
    dispatch(setSavePendingState(exercise, true));
    const doSave = () => { 
      dispatch(saveExercise(exercise))
        .then(() => dispatch(fetchExerciseJSON(exercise)))
        .then(
      res => dispatch(fetchSameFolder(exercise, state.get('folder') ))
    );
    }
    _.delay(doSave, 2000); //Make sure that all parsing is done and the XML state is updated. This should be done by inspecting the state but for the moment this provides a safety net.
  }
}
function handleReset(exercise) {
  throttleParseXML.cancel(); //Cancel possibly queued XML parsing updates
  return (dispatch, getState) => {
    dispatch(setResetPendingState(exercise, true))
    dispatch(updatePendingStateIn( ['exercises', exercise, 'loadingJSON'], true));
    return dispatch(resetExercise(exercise))
      .then( () => dispatch(setResetPendingState(exercise, false)))
      .then( () => dispatch(setExerciseModifiedState(exercise, false)))
      .then( () => dispatch(updatePendingStateIn( ['exercises', exercise, 'loadingJSON'], false)));
  }
}

const mapStateToProps = state => {
  var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));
  var activeCourse = state.getIn(['activeCourse'])
  return ({
  activeCourse: activeCourse,
  username: state.getIn(['login', 'username']),
  course: state.getIn(['courses', activeCourse, 'course_name'], ""),
  motd: state.getIn(['courses',activeCourse,'motd'], ""),
  groups: state.getIn(['login', 'groups'], immutable.List([])),
  admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
  viewer: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
  author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
  activeExercise: state.get('activeExercise'),
  exerciseState: activeExerciseState,
  activeAdminTool: state.get('activeAdminTool'),
  folder: state.get('folder', ""),
  pendingState: state.get('pendingState'),
  menuPath: state.get('menuPath'),
  languages:  state.getIn(['course', 'languages'],['none']),
  compactview: state.getIn(['login','compactview'] , true),
  lti_login: state.getIn(['login','lti_login'] , true),

});
}

const mapDispatchToProps = dispatch => ({
  onXMLEditorClick: (event) => dispatch(updateActiveAdminTool('xml-editor')),
    onOptionsClick: (event) => dispatch(updateActiveAdminTool('options')),
    onStatisticsClick: (event) => dispatch(updateActiveAdminTool('statistics')),
    onSave: (exercise) => dispatch(handleSave(exercise)),
    onReset: (exercise) => dispatch(handleReset(exercise)),
    onHome: () => dispatch(navigateMenuArray([])),
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseLoginInfo)
export {Tools,handleReset,handleSave}
