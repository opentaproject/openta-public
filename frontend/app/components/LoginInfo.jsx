import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercises, 
  fetchExerciseXML,
  fetchExercise,
  fetchSameFolder,
  saveExercise,
} from '../fetchers.js';

import {
  updateActiveAdminTool
} from '../actions.js';

import immutable from 'immutable';
import {SUBPATH} from '../settings.js';

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

var Tools = ({showsave, onsave, savepending, savesuccess, saveerror, showreset, resetpending, onreset}) => (
    <div className="uk-button-group"> 
        { showsave && <a className={"uk-button uk-button-small " + (saveerror ? "uk-button-danger" : "uk-button-success")} onClick={onsave}>Save {savepending ? (<i className="uk-icon-cog uk-icon-spin"></i>) : (<i className="uk-icon-floppy-o"></i>)} </a> }
        { showreset && savepending !== true && <a className="uk-button uk-button-small uk-button-primary uk-margin-right" onClick={onreset}> {resetpending ? (<i className="uk-icon-cog uk-icon-spin"></i>) : (<i className="uk-icon-undo"></i>)}</a> }
    </div>
);

const BaseLoginInfo = ({ username,groups, admin, author, activeExercise, exerciseState, activeAdminTool, onXMLEditorClick, onOptionsClick, onSave, onReset}) => {
    var savePending = exerciseState.get('savepending');
    var saveError = exerciseState.get('saveerror');
    var resetPending = exerciseState.get('resetpending');
    var modified = exerciseState.get('modified');
    //var loading = pendingState.getIn(['exercises', key, 'loadingXML'],false);
  var admintoolsmenu = [
    {
      id: 'xml-editor',
      name: 'XML Editor',
      reqGroup: 'Author',
      callback: onXMLEditorClick
    },
    {
      id: 'options',
      name: 'Options',
      reqGroup: 'Admin',
      callback: onOptionsClick
    }
  ];
  var permanentitems = admintoolsmenu.map( item => {
    if(groups.includes(item.reqGroup)) {
    var cssclass = "uk-button uk-button-primary" + (activeAdminTool === item.id ? " uk-active" : "");
    return ( <a key={item.id} className={cssclass} onClick={item.callback}>{item.name}</a> );
    }
    else
      return (<span/>)
  });

  var savereset = (
          <Tools showsave={modified} savepending={savePending} savesuccess={!modified && saveError === false} showreset={modified} saveerror={saveError} resetpending={resetPending} onsave={(event) => onSave(activeExercise)} onreset={(event) => onReset(activeExercise)}/>
  );
  var admintools = (
    <div className="uk-button-group uk-margin-left">
      {permanentitems}
    </div>
  );
  var renderGroupIcons = groups.map( group => {
                                    if(group in groupIcons)
                                      return (<i className={"uk-icon uk-text-success uk-margin-small-left " + groupIcons[group].icon} title={groupIcons[group].alt}/>)
                                    else
                                      return (<span/>)
  });
return (
  <nav id="login" className="uk-nav uk-navbar-attached ta-nav border-bottom">
  <div className="uk-container uk-container-center">
  { activeExercise &&
  <div className="uk-navbar-content">
    <a href="#offcanvas-exercise-list" className="uk-navbar-toggle exercise-list-off-canvas" data-uk-offcanvas/>
  </div> }
  <div className="uk-navbar-brand exercise-list-on-canvas"><i className="uk-icon uk-icon-medium uk-icon-circle-o"></i><span className="uk-text-small uk-text-middle"> OpenTA</span></div>
  <div className="uk-navbar-flip">
  <div className="uk-navbar-content">
  { author && activeExercise && savereset}
  </div>
  <ul className="uk-navbar-nav">
      <li>
      <a href={SUBPATH + "/logout/?next=" + SUBPATH + "/login"}><i className="uk-icon uk-icon-sign-out uk-text-large uk-text-middle"></i></a>
      </li>
  </ul>
  </div>
  <div className="uk-navbar-content uk-navbar-center">
  {renderGroupIcons} <span className="uk-text-large uk-text-middle">{username}</span>{ admin ? ( <span className="uk-text-small uk-text-middle"> (admin)</span> ) : "" }
  { activeExercise && admintools }
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
  activeExercise: PropTypes.string,
  exerciseState: PropTypes.object,
  activeAdminTool: PropTypes.string,
  onXMLEditorClick: PropTypes.func,
  onOptionsClick: PropTypes.func
};

function handleSave(exercise) {
  return (dispatch, getState) => {
    console.log("Save " + exercise);
    dispatch(saveExercise(exercise)).then(
      res => dispatch(fetchSameFolder(exercise, getState().get('folder') ))
    );
    console.log([exercise, getState().get('folder')]);
  }
}
function handleReset(exercise) {
  return (dispatch, getState) => {
    console.log("Reset " + exercise);
    dispatch(fetchExercise(exercise, true));
  }
}

const mapStateToProps = state => {
  var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));
  return ({
  username: state.getIn(['login', 'username']),
  groups: state.getIn(['login', 'groups'], immutable.List([])),
  admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
  author: state.getIn(['login', 'groups'],immutable.List([])).includes('Author'),
  activeExercise: state.get('activeExercise'),
  exerciseState: activeExerciseState,
  activeAdminTool: state.get('activeAdminTool'),
  folder: state.get('folder', ""),
});
}

const mapDispatchToProps = dispatch => ({
  onXMLEditorClick: (event) => dispatch(updateActiveAdminTool('xml-editor')),
    onOptionsClick: (event) => dispatch(updateActiveAdminTool('options')),
    onSave: (exercise) => dispatch(handleSave(exercise)),
    onReset: (exercise) => dispatch(handleReset(exercise)),
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseLoginInfo)
