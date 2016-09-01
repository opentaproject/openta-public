import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import _ from 'lodash';
import immutable from 'immutable';
import XMLEditor from './XMLEditor.jsx';
import xml2js from 'xml2js';
import Spinner from './Spinner.jsx';

import Exercise from './Exercise';

import { 
  updateQuestionResponse, 
  updateExerciseXML, 
  updateExerciseJSON,
  setExerciseModifiedState
} from '../actions.js';
import {
  saveExercise,
  fetchExercise
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
  childkey: '$children$',
  strict: true
  //attrNameProcessors: [ (name) => '@' + name ]
});

var throttleParseXML = _.throttle(XMLParser.parseString, 1000);

var Tools = ({showsave, onsave, savepending, savesuccess, saveerror, showreset, resetpending, onreset}) => (
  <div>
    <div className="uk-button-group"> 
        { showsave && <a className={"uk-button uk-button-small " + (saveerror ? "uk-button-danger" : "uk-button-success")} onClick={onsave}>Save {savepending ? (<i className="uk-icon-cog uk-icon-spin"></i>) : (<i className="uk-icon-floppy-o"></i>)} </a> }
        { showreset && savepending !== true && <a className="uk-button uk-button-small uk-button-primary uk-margin-right" onClick={onreset}> {resetpending ? (<i className="uk-icon-cog uk-icon-spin"></i>) : (<i className="uk-icon-undo"></i>)}</a> }
    </div>
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
  pendingState: PropTypes.object
};

  render() {
    var key = this.props.exerciseKey;
    var exerciseState = this.props.exerciseState;
    var pendingState = this.props.pendingState;
    var exercisexml = exerciseState.get('xml','');
    var onSave = this.props.onSave;
    var onReset = this.props.onReset;
    var savePending = exerciseState.get('savepending');
    var saveError = exerciseState.get('saveerror');
    var resetPending = exerciseState.get('resetpending');
    var modified = exerciseState.get('modified');
    var loading = pendingState.getIn(['exercises', key, 'loadingXML'],false);
    var authorDOM = (
    <ul className="uk-grid uk-grid-width-xlarge-1-2">
        <li key="exercise">
          <Tools showsave={modified} savepending={savePending} savesuccess={!modified && saveError === false} showreset={modified} saveerror={saveError} resetpending={resetPending} onsave={(event) => onSave(key)} onreset={(event) => onReset(key)}/>
          <Exercise/>
        </li>
        <li key="xml">
        { loading && <Spinner/> }
        { !loading && <XMLEditor xmlCode={exercisexml} onChange={ (xml) => this.props.onXMLChange(xml, key)}/> }
        </li>
        </ul>
    );
    return key ? authorDOM : (<span/>);
  }
}

function handleXMLChange(dispatch, xml, exercise) {
  dispatch(updateExerciseXML(exercise, xml));
  XMLParser.reset();
  throttleParseXML(xml, (err, result) => {
    if(err || result === null) {
      console.dir(err);
    }
    else {
      var questions = _.get(result, 'exercise.question', {});
      if(questions.constructor !== Array)
        _.set(result, 'exercise.question', [questions]);

      dispatch(updateExerciseJSON(exercise, result));
      dispatch(setExerciseModifiedState(exercise, true));
    }
  });
}

function handleSave(dispatch, exercise) {
  console.log("Save " + exercise);
  dispatch(saveExercise(exercise));
}
function handleReset(dispatch, exercise) {
  console.log("Reset " + exercise);
  dispatch(fetchExercise(exercise, true));
}

const mapStateToProps = state => {
  //var activeExerciseState = _.get(state.exerciseState, state.activeExercise, {});
  var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));
  return (
  {
    exerciseKey: state.get('activeExercise'),
    exerciseState: activeExerciseState,
    pendingState: state.get('pendingState')
  })
};

const mapDispatchToProps = dispatch => {
  return {
    onXMLChange: (xml, exercise) => handleXMLChange(dispatch, xml, exercise) ,
    onSave: (exercise) => handleSave(dispatch, exercise),
    onReset: (exercise) => handleReset(dispatch, exercise)
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseAuthorExercise)
