import React, { Component, Suspense } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import Alert from './Alert.jsx';
import EditExerciseOptions from './EditExerciseOptions.jsx';
import _ from 'lodash';
import immutable from 'immutable';
import XMLEditor from './XMLEditor.jsx';
import Statistics from './Statistics.jsx';
import ExerciseRecentResults from './ExerciseRecentResults.jsx';
import ExerciseAnalyze from './ExerciseAnalyze.jsx';
import ExerciseRegrade from './ExerciseRegrade.jsx';
import xml2js from 'xml2js';
import Spinner from './Spinner.jsx';
import Audit from './Audit.jsx';
import AuditOverview from './AuditOverview.jsx';
import AuditCompactList from './AuditCompactList.jsx';
import Assets from './Assets.jsx';

import Exercise from './Exercise';
import { menuPositionAt, menuPositionUnder } from '../menu.js';
import { getcookie } from '../cookies.js';

import { fetchSetSelectedExercises } from '../fetchers/exercise.js';

import {
  updateExerciseActiveXML,
  updateExerciseJSON,
  updatePendingStateIn,
  setExerciseModifiedState,
  setExerciseXMLError
} from '../actions.js';
import { fetchExercise, fetchExerciseRemoteState, fetchSameFolder, fetchExerciseTree } from '../fetchers.js';

function LazyXMLEditor() {
  return (
    <div>
      <Suspense fallback={<div>Loading...</div>}>
        <XMLEditor />
      </Suspense>
    </div>
  );
}

var XMLParser = new xml2js.Parser({
  trim: true,
  explicitArray: false,
  explicitCharkey: true,
  charkey: '$',
  attrkey: '@attr',
  explicitChildren: true,
  preserveChildrenOrder: true,
  charsAsChildren: true,
  childkey: '$children$',
  strict: true,
  async: false, // set to true caused fail in v421
  chunkSize: 1000
});

var unstableKey = 0;
const nextUnstableKey = () => unstableKey++;
var resetAndParse = (string, func) => {
  XMLParser.reset();
  var res = XMLParser.parseString(string, func);
};

var throttleParseXML = _.throttle(resetAndParse, 2000);

var Tools = ({ savepending, savesuccess, saveerror }) => (
  <div>
    {saveerror && !savepending && (
      <div className="uk-badge uk-badge-danger uk-margin-right">
        Error while saving, try again or consider manual backup.
      </div>
    )}
    {savesuccess && <div className="uk-badge uk-badge-success">Saved</div>}
  </div>
);

class BaseAuthorExercise extends Component {
  constructor(props) {
    super();
    this.state = {
      xml: props.exerciseState.get('activeXML', '')
    };
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
    subdomain: PropTypes.string,
    showXML : PropTypes.bool,
  };

  render() {
    var key = this.props.exerciseKey;
    var exerciseState = this.props.exerciseState;
    var pendingState = this.props.pendingState;
    var xmlError = this.props.xmlError;
    var savePending = exerciseState.get('savepending');
    var saveError = exerciseState.get('saveerror');
    var modified = exerciseState.get('modified');
    var loadingXML = pendingState.getIn(['exercises', key, 'loadingXML'], false);
    var gridClass = this.props.atMenu(['activeExercise', 'assets']) ? '' : 'admin';
    var canViewXML = this.props.author || this.props.view;
    var showxml =  !loadingXML && this.props.atMenu(['activeExercise', 'xmlEditorSplit']) && canViewXML 
    var showXML = this.props.showXML;
    if ( showXML ){
	    var showxml = showXML;
	    var widthclass = 'uk-width-1-1'
    }	else {
	    var widthclass = 'exercise-admin'
    }
    var authorDOM = (
      <div className="uk-grid uk-padding-large uk-width-1-1">
        {!this.props.underMenu(['activeExercise', 'audit']) && (
          <div className="uk-width-1-1">
            <div className="uk-panel uk-panel-box">
              {' '}
              <Assets />
            </div>
          </div>
        )}
        {!this.props.underMenu(['activeExercise', 'audit']) &&
          !this.props.atMenu(['activeExercise', 'xmlEditor']) &&
          !this.props.atMenu(['activeExercise', 'assets']) && (
            <div key={key + 'exercise-admin'} className="exercise-admin">
              <Tools savepending={savePending} savesuccess={!modified && saveError === false} saveerror={saveError} />
              <Exercise />
            </div>
          )}

        {!this.props.atMenu(['activeExercise', 'xmlEditor']) &&
          !this.props.underMenu(['activeExercise', 'audit']) &&
          !this.props.atMenu(['activeExercise', 'assets']) && (
            <div key="xml-author-exercise" className="xmleditor">
              {loadingXML && this.props.atMenu(['activeExercise', 'xmlEditorSplit']) && <Spinner />}
              {showxml && ( <XMLEditor xmlCode={this.state.xml} onChange={(editor, data, xml) => this.xmlUpdate(xml, key)} />)}
              {xmlError && this.props.atMenu(['activeExercise', 'xmlEditorSplit']) && (
                <Alert type="error">{xmlError}</Alert>
              )}
              {this.props.atMenu(['activeExercise', 'options']) && this.props.admin && (
                <div>
                  <EditExerciseOptions exerciseKey={this.props.exerciseKey} />
                </div>
              )}
              {this.props.atMenu(['activeExercise', 'statistics']) &&
                (this.props.view || this.props.admin || this.props.author) && <Statistics />}
              {this.props.atMenu(['activeExercise', 'recent']) &&
                (this.props.view || this.props.admin || this.props.author) && <ExerciseRecentResults />}
              {this.props.atMenu(['activeExercise', 'regrade']) && (this.props.view || this.props.admin) && (
                <ExerciseRegrade />
              )}
		{this.props.atMenu(['activeExercise', 'analyze']) && (this.props.view || this.props.admin) && (
                <ExerciseAnalyze/>
              )}
            </div>
          )}
        {loadingXML && this.props.atMenu(['activeExercise', 'xmlEditor']) && <Spinner />}
        {!loadingXML && this.props.atMenu(['activeExercise', 'xmlEditor']) && canViewXML && (
          <div className="uk-width-1-1">
            <div className="uk-flex">
              <div style={{ flex: '1' }}>
                <XMLEditor xmlCode={this.state.xml} onChange={(editor, data, xml) => this.xmlUpdate(xml, key)} />
                {xmlError && this.props.atMenu(['activeExercise', 'xmlEditor']) && (
                  <Alert type="error">{xmlError}</Alert>
                )}
              </div>
            </div>
          </div>
        )}
        {this.props.underMenu(['activeExercise', 'audit', 'myaudits']) && (
          <div className="uk-width-1-1 uk-padding-remove">
            <AuditCompactList />
            <Audit />
          </div>
        )}
        {this.props.underMenu(['activeExercise', 'audit', 'overview']) && this.props.admin && <AuditOverview />}
      </div>
    );
    return key ? authorDOM : <span />;
  }

  handleIframeLoad = (event, onOptionsSubmit, onOptionsLoad) => {
    var submitted_cookie = getcookie('submitted', event.target.contentDocument);
    if (submitted_cookie.length > 0 && submitted_cookie[0] === 'true') {
      onOptionsSubmit();
    }
    onOptionsLoad(this.props.selectedExercises);
  };

  xmlUpdate = (xml, exercise) => {
    this.setState({ xml: xml });
    this.props.onXMLChange(xml, exercise);
  };

  componentDidUpdate = (props, state, root) => {
    //Check if the exercise XML changed from the store (i.e. active exercise changed or reset of current) and update to the corresponding working state XML
    // Use a props function to dispatch XML parse?
    if (props.exerciseState.get('xml') !== this.props.exerciseState.get('xml')) {
      this.setState({ xml: this.props.exerciseState.get('activeXML', '') });
      this.props.onXMLChange(this.props.exerciseState.get('activeXML', ''), this.props.exerciseKey, false);
    }
  };
}

function handleXMLChange(xml, exercise, flagModified = true) {
  return (dispatch) => {
    throttleParseXML(xml, (err, result) => {
      dispatch(updateExerciseActiveXML(exercise, xml));
      dispatch(updatePendingStateIn(['exercises', exercise, 'xmlParse'], false));
      if (err || result === null) {
        if (err && err.message) {
          var re = /\sLine: ([0-9]*)/;
          var line = err.message.match(re);
          if (line) {
            var formatted = err.message.replace(re, '. ( Around line: ' + (parseInt(line[1]) + 1));
            dispatch(setExerciseXMLError(exercise, formatted + ' )'));
          } else {
            dispatch(setExerciseXMLError(exercise, err.message));
          }
        } else {
          dispatch(setExerciseXMLError(exercise, 'Unknown error in parsing XML.'));
        }
      } else {
        var questions = _.get(result, 'exercise.question', {});
        var global = _.get(result, 'exercise.global', {});
        if (questions.constructor !== Array) {
          _.set(result, 'exercise.question', [questions]);
        }
        if (global.constructor !== Array) {
          _.set(result, 'exercise.global', [global]);
        }

        dispatch(updateExerciseJSON(exercise, result));
        if (flagModified) {
          dispatch(setExerciseModifiedState(exercise, true));
        }
        dispatch(setExerciseXMLError(exercise, null));
      }
    });
  };
}

function handleOptionsSubmit() {
  return (dispatch, getState) => {
    var coursePk = getState().get('activeCourse');
    var subdomain = getState().get('subdomain');
    var exercise = getState().get('activeExercise');
    dispatch(fetchExercise(exercise, true));
    dispatch(fetchExerciseRemoteState(exercise));
    dispatch(fetchSameFolder(exercise, subdomain));
    dispatch(fetchExerciseTree(coursePk));
  };
}

const mapStateToProps = (state) => {
  //var activeExerciseState = _.get(state.exerciseState, state.activeExercise, {});
  var activeExerciseState = state.getIn(['exerciseState', state.get('activeExercise')], immutable.Map({}));
  return {
    exerciseKey: state.get('activeExercise'),
    exerciseState: activeExerciseState,
    pendingState: state.get('pendingState'),
    activeAdminTool: state.get('activeAdminTool'),
    admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
    author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
    view: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
    atMenu: (path) => menuPositionAt(state.get('menuPath'), path),
    underMenu: (path) => menuPositionUnder(state.get('menuPath'), path),
    xmlError: activeExerciseState.has('xmlError') ? activeExerciseState.get('xmlError') : null,
    exercises: state.getIn(['exerciseState'], immutable.List([])),
    selectedExercises: state.getIn(['selectedExercises'], immutable.List([])),
    selectedExercisesMeta: state.getIn(['selectedExercisesMeta'], immutable.List([]))
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    onXMLChange: (xml, exercise, flagModified = true) => dispatch(handleXMLChange(xml, exercise, flagModified)),
    onOptionsSubmit: () => dispatch(handleOptionsSubmit()),
    onOptionsLoad: (exercises) => dispatch(fetchSetSelectedExercises(exercises))
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseAuthorExercise);
export { throttleParseXML }; //Give other modules the possibility to cancel the queued actions form the throttled parsing
