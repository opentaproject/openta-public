import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import _ from 'lodash';
import immutable from 'immutable';
import XMLEditor from './XMLEditor.jsx';
import Statistics from './Statistics.jsx';
import ExerciseRecentResults from './ExerciseRecentResults.jsx';
import xml2js from 'xml2js';
import Spinner from './Spinner.jsx';
import Audit from './Audit.jsx';

import Exercise from './Exercise';
import { menuPositionAt } from '../menu.js';
import {getcookie} from '../cookies.js';
import {SUBPATH} from '../settings.js';

import { 
  updateQuestionResponse, 
  updateExerciseXML, 
  updateExerciseJSON,
  setExerciseModifiedState
} from '../actions.js';
import {
  saveExercise,
  fetchExercise,
  fetchExerciseRemoteState,
  fetchSameFolder,
} from '../fetchers.js';

var XMLParser = new xml2js.Parser({
  trim:true,
  explicitArray: false,
  explicitCharkey: true,
  charkey: '$',
  attrkey: '@attr',
  //mergeAttrs: true,
  explicitChildren: true,
  preserveChildrenOrder: true,
  charsAsChildren: true,
  childkey: '$children$',
  strict: true
  //attrNameProcessors: [ (name) => '@' + name ]
});

var throttleParseXML = _.throttle(XMLParser.parseString, 1000);

var Tools = ({savepending, savesuccess, saveerror}) => (
  <div>
      { saveerror && !savepending && (<div className="uk-badge uk-badge-danger uk-margin-right">Error while saving, try again or consider manual backup.</div>) }
      { savesuccess && (<div className="uk-badge uk-badge-success">Saved</div>) }
  </div>
);

class BaseAuthorExercise extends Component {
  constructor() {
    super();
  } 

  static propTypes = {
  exerciseKey: PropTypes.string.isRequired,
  onSave: PropTypes.func,
  onReset: PropTypes.func,
  onXMLChange: PropTypes.func,
  exerciseState: PropTypes.object,
  pendingState: PropTypes.object,
  activeAdminTool: PropTypes.string,
  atMenu: PropTypes.func,
  admin: PropTypes.bool,
  author: PropTypes.bool,
  view: PropTypes.bool,
};

  render() {
    var key = this.props.exerciseKey;
    var exerciseState = this.props.exerciseState;
    var pendingState = this.props.pendingState;
    var exercisexml = exerciseState.get('xml','');
    var savePending = exerciseState.get('savepending');
    var saveError = exerciseState.get('saveerror');
    var modified = exerciseState.get('modified');
    var loadingXML = pendingState.getIn(['exercises', key, 'loadingXML'],false);
    var authorDOM = (
      <div className="uk-grid admin">
        { !this.props.atMenu(['activeExercise', 'audit']) &&
        <div key="exercise" className="exercise-admin">
          <Tools savepending={savePending} savesuccess={!modified && saveError === false} saveerror={saveError} />
          <Exercise/>
        </div>
        }
        <div key="xml" className="xmleditor">
        { loadingXML && this.props.atMenu(['activeExercise','xmlEditor']) && <Spinner/> }
        { !loadingXML && this.props.atMenu(['activeExercise','xmlEditor']) && this.props.author && <XMLEditor xmlCode={exercisexml} onChange={ (xml) => this.props.onXMLChange(xml, key)}/> }
        { this.props.atMenu(['activeExercise','options']) && this.props.admin && 
          <div className="uk-panel uk-panel-box uk-panel-box-secondary uk-margin-top">
            <iframe key={key} scrolling="no" className="options" src={SUBPATH + "/exercise/" + key + "/editmeta"} onLoad={event => this.handleIframeLoad(event, this.props.onOptionsSubmit)}/> 
            </div>
        }
        { this.props.atMenu(['activeExercise','statistics']) && this.props.view && <Statistics/> }
        { this.props.atMenu(['activeExercise','recent']) && this.props.view && <ExerciseRecentResults/> }
        </div>
        { this.props.atMenu(['activeExercise','audit']) && this.props.admin && <Audit/> }
      </div>
    );
    return key ? authorDOM : (<span/>);
  }

  handleIframeLoad = (event, onOptionsSubmit) => {
    var submitted_cookie = getcookie('submitted', event.target.contentDocument);
    if(submitted_cookie.length > 0 && submitted_cookie[0] === 'true')
      onOptionsSubmit()
  }

  componentDidMount = (props,state,root) => {
    if(this.iframeref) {
      this.iframeref.onload = () => console.dir(this)
    }
  }
}

function handleXMLChange(dispatch, xml, exercise) {
  dispatch(updateExerciseXML(exercise, xml));
  XMLParser.reset();
  throttleParseXML(xml, (err, result) => {
    if(err || result === null) {
      //console.dir(err);
    }
    else {
      var questions = _.get(result, 'exercise.question', {});
      var global = _.get(result, 'exercise.global', {});
      if(questions.constructor !== Array)
        _.set(result, 'exercise.question', [questions]);
      if(global.constructor !== Array)
        _.set(result, 'exercise.global', [global]);

      dispatch(updateExerciseJSON(exercise, result));
      dispatch(setExerciseModifiedState(exercise, true));
    }
  });
}

function handleOptionsSubmit() {
  return (dispatch, getState) => {
    var folder = getState().get('folder');
    var exercise = getState().get('activeExercise');
    dispatch(fetchExercise(exercise, true));
    dispatch(fetchExerciseRemoteState(exercise));
    dispatch(fetchSameFolder(exercise, folder));
  }
}

const mapStateToProps = state => {
  //var activeExerciseState = _.get(state.exerciseState, state.activeExercise, {});
  var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));
  return (
  {
    exerciseKey: state.get('activeExercise'),
    exerciseState: activeExerciseState,
    pendingState: state.get('pendingState'),
    activeAdminTool: state.get('activeAdminTool'),
    admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
    author: state.getIn(['login', 'groups'],immutable.List([])).includes('Author'),
    view: state.getIn(['login', 'groups'],immutable.List([])).includes('View'),
    atMenu: (path) => menuPositionAt( state.get('menuPath'), path ),
  })
};

const mapDispatchToProps = dispatch => {
  return {
    onXMLChange: (xml, exercise) => handleXMLChange(dispatch, xml, exercise) ,
    onOptionsSubmit: () => dispatch(handleOptionsSubmit()),
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseAuthorExercise)
