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

const BaseLoginInfo = ({ username, groups, iframed, replyTo, admin, author, viewer, activeExercise,
      onHome, pendingState, menuPath, motd, lti_login, course, openTAVersion}) => {
  var renderGroupIcons = groups.map( group => {
                                    if(group in groupIcons)
                                      return (<i key={group} className={"uk-icon uk-text-success uk-margin-small-left " + groupIcons[group].icon} title={groupIcons[group].alt}/>)
                                    else
                                      return (<span key={group}/>)
  });
  var renderPending = pendingPaths.map( item => {
    return (pendingState.getIn(item.path, false) && (<span key={item.path}>{item.name}<Spinner icon="uk-icon-bar-chart" size="" className="uk-margin-small-left"/></span>))
  });
  var studentViewDOM = (author || viewer) ? (<button onClick={(e) => UIkit.modal.confirm("View site as student?", () => window.open(SUBPATH + "/hijack/username/student", "_self"))} className="uk-button uk-button-mini uk-alert-warning" data-uk-tooltip title="Log in as default student">Student view</button>) : '';
var canViewXML = author || viewer || admin
  return (
    <nav id="login" className="uk-nav uk-navbar-attached ta-nav border-bottom">
      <div className="uk-container uk-container-center" style={{maxWidth: 'none'}}>
        {/* Username and side-bar menu */}
        <div className="uk-navbar-content uk-flex uk-flex-wrap">
          {/* Side-bar menu and home button */}
          {activeExercise && menuPositionUnder(menuPath, ['activeExercise']) &&
            <div className="uk-navbar-content uk-padding-remove">
              <a href="#offcanvas-exercise-list" className="uk-navbar-toggle exercise-list-off-canvas uk-padding-remove" data-uk-offcanvas />
            </div>}
          <ul className="uk-navbar-nav exercise-list-on-canvas"><li>
            <a className="uk-navbar-brand onHome Home" onClick={onHome}>
              <i className="uk-icon uk-icon-small uk-icon-mail-reply"></i>
            </a>
          </li></ul>
          {/* Username */}
          <div className="uk-vertical-align">
            <span className="uk-vertical-align-middle">
              {renderGroupIcons}
              <span className="uk-text-middle">{username}</span>
              <span className="uk-text-middle uk-text-warning"> {motd} </span>
            </span>
          </div>
        </div>
        {/* Main navbar */}
        <div className="uk-navbar-flip">
          <ul className="uk-navbar-nav">
            {author && (
              <li>
                <div className="uk-navbar-content uk-visible-large"> {studentViewDOM} </div>
                <div className="uk-navbar-content uk-hidden-large uk-hidden smallHidden"> {studentViewDOM} </div>
              </li>
            )}
            <li>
              <div className="uk-navbar-content">
                <LanguageSelect />
              </div>
            </li>
            {author && (
              <li>
                <div className="uk-navbar-content uk-visible-large">
                  <CourseSelect />
                </div>
                <div className="uk-navbar-content uk-hidden-large uk-hidden smallHidden">
                  <CourseSelect />
                </div>
              </li>
            )
            }
            <li>
              <a href={"mailto:" + replyTo + "?subject=" + openTAVersion} className="uk-padding-remove"
                data-uk-tooltip title={ "Send an email to " + replyTo + " and include that this is OpenTA version [" + openTAVersion + "]" }>
                <span className="uk-icon-question-circle"></span>
              </a>
            </li>
            {lti_login && (
              <li>
                <a title="Change password" href={SUBPATH + "/change_password/?next="}><i className="uk-icon uk-icon-key uk-text-medium"></i></a>
              </li>
            )}
            {/* Don't show administration link when in iframe */}
            {admin && (!iframed) && (
              <li>
                <a title="Administration" href={SUBPATH + "/administration/"}><i className="uk-icon uk-icon-cog uk-text-middle"></i></a>
              </li>
            )}
            {!iframed && (
              <li >
                <a title="Logga ut" href={SUBPATH + "/logout/" + course + '/'}><span className="uk-padding-large"> {course} </span><i className="uk-icon uk-icon-sign-out uk-text-large uk-text-middle"></i></a>
              </li>
            )}
            {iframed && (
              <li >
                <a title="Logga ut" href={SUBPATH + "/logout/" + course + '/lti_login/'}><span className="uk-padding-large"> {course} </span><i className="uk-icon uk-icon-rotate-right uk-text-large uk-text-middle"></i></a>
              </li>
    ) }

            {/* TODO: Is this needed? Edit profile */}
            {/* {false && lti_login && (
              <li>
                <a title="Edit profile" href={SUBPATH + "/edit_profile/?next="}><i className="uk-icon uk-icon-user uk-text-large uk-text-middle"></i></a>

              </li>
            )} */}

          </ul>
        </div>

        {/* Admin menu bar */}
        <div className="uk-navbar-content uk-margin-small-top uk-flex uk-flex-middle uk-flex-wrap uk-visible-large" style={{ height: 'auto' }}>
          {renderPending}
          {canViewXML && <Menu />}
        </div>
        {/* Toggle menu for smaller sizes */}
        { canViewXML && (
          <span>
          <button className="uk-button uk-button-mini uk-margin-small-top uk-hidden-large" data-uk-toggle="{target:'.smallHidden'}"><i className="uk-icon-ellipsis-v"/></button>
          <div className="uk-navbar-content uk-margin-small-top uk-flex uk-flex-middle uk-flex-wrap uk-hidden-large uk-hidden smallHidden" style={{ height: 'auto' }}>
            {renderPending}
            {canViewXML && <Menu />}
          </div>
          </span>
        )}
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
  iframed: PropTypes.bool,
  lti_login: PropTypes.bool,

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
  replyTo: state.getIn(['courses', activeCourse, 'email_reply_to'], ""),
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
  iframed: state.getIn(['iframed'] , false),
  openTAVersion: state.getIn(['openTAVersion'], 'VERSION MISSING'),
  lti_login: state.getIn(['login','lti_login'], false)

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
