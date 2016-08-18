import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import XMLEditor from './XMLEditor.jsx';
import xml2js from 'xml2js';
import _ from 'lodash';
import immutable from 'immutable';
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
  attrkey: '@',
  mergeAttrs: true,
  attrNameProcessors: [ (name) => '@' + name ]
});

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

class BaseExercise extends Component {
  constructor() {
    super();
  } 

  static propTypes = {
  exerciseName: PropTypes.string.isRequired,
  onQuestionInputKeyUp: PropTypes.func,
  onSave: PropTypes.func,
  onReset: PropTypes.func,
  onXMLChange: PropTypes.func,
  exerciseState: PropTypes.object
};

  render() {
    var exerciseState = this.props.exerciseState;
    var exercisejson = exerciseState.get('json', immutable.Map({}) );
    var exercisexml = exerciseState.get('xml','');//_.get(this.props.exerciseState, "xml", '');
    var figure = exercisejson.getIn(['problem','figure','$']);//this.props.exercisejson.problem ? exercisejson.problem.figure[0] : "";
    var name = this.props.exerciseName;
    var renderName = exercisejson.getIn(['problem','name','$'], "No name");
    var renderText = exercisejson.getIn(['problem','question','text','$'], "");
    var onQuestionInputKeyUp = this.props.onQuestionInputKeyUp;
    var onSave = this.props.onSave;
    var onReset = this.props.onReset;
    var savePending = exerciseState.get('savepending');
    var saveError = exerciseState.get('saveerror');
    var resetPending = exerciseState.get('resetpending');
    var modified = exerciseState.get('modified');
    var questions = [];
    if(exercisejson.has('problem')) {
      questions = exercisejson.getIn(['problem','thecorrectanswer'],{}).rest().map( (q, index_) => {
        var index = index_ + 1;
        var alerts = exerciseState.getIn(['question',index.toString(),'alerts'],immutable.List([])).toList()
          .map( (alert, alertindex) => (<Alert message={alert.get('message')} type={alert.get('type')} key={alertindex}/>) );
        return (
          <div>
          <h3>Test</h3>
          <div className="uk-block uk-block-primary uk-contrast uk-margin-top uk-padding-top-remove" key={index}>
          {/*<div className="uk-panel uk-panel-box uk-panel-box-primary uk-margin-top uk-border-rounded" key={index}>*/}
              <div className="uk-container">
              <label className="uk-form-row">{q.getIn(['@question'],'')}</label>
              <div className="uk-form-icon uk-width-1-1">
                <i className="uk-icon-pencil"/>
                <input className="uk-width-1-1" type="text" onKeyUp={(event) => onQuestionInputKeyUp(Object.assign({}, event), name, index)}></input>
              </div>
              {alerts}
              </div>
          </div>
          </div>
      )
      } );
    }
    var exerciseDOM = (
        <ul className="uk-grid uk-grid-width-xlarge-1-2">
        <li key="exercise">
        <article className="uk-article uk-margin-top" ref="exercise" key={name}>
          <div className="uk-grid">
          <h1 className="uk-article-title">{renderName}</h1>
          <Tools showsave={modified} savepending={savePending} savesuccess={!modified && saveError === false} showreset={modified} saveerror={saveError} resetpending={resetPending} onsave={(event) => onSave(name)} onreset={(event) => onReset(name)}/>
          </div>
          <div className="uk-clearfix">
            <div className="uk-align-medium-right">
            { figure && <img style={{maxHeight: '100pt'}} src={'http://localhost:8000/exercise/' + name + '/asset/' + figure} alt=""/> }
            </div>
            <span dangerouslySetInnerHTML={{__html: renderText}} />
          </div>
          <hr className="uk-article-divider"/>
          <form className="uk-form" onSubmit={(event) => event.preventDefault()}>
          {questions}
          </form>
        </article>
        </li>
        <li key="xml">
        <XMLEditor xmlCode={exercisexml} onChange={ (xml) => this.props.onXMLChange(xml, name)}/>
        </li>
        </ul>
    );
    return (
      <div className="uk-width-medium-5-6">
      {name ? exerciseDOM : ""}
      </div>
    );
  }

  componentDidUpdate(props,state,root) {
    var node = ReactDOM.findDOMNode(this.refs.exercise);
    MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
  }
}

function checkQuestion(exercise, question, expression) {
  return dispatch => {
    var payload = {
      expression: expression
    }
    //var data = new FormData();
    //data.append('json', new Blob([JSON.stringify(payload)], {type: 'application/json'}));
    var data = JSON.stringify(payload);
    var fetchconfig = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: data
    }
      
    fetch('http://localhost:8000/exercise/' + exercise + '/question/' + question + '/check', fetchconfig)
    .catch( err => console.log("checkQuestion error!") )
    .then(res => res.json())
    .then(json => { dispatch(updateQuestionResponse(exercise, question, json)); return json});
    //.then(json => console.dir(json))
  }
}

function handleQuestionInputKeyUp(dispatch, event, exercise, question) {
  if(event.keyCode == 13) {
    dispatch(checkQuestion(exercise, question, event.target.value));
  }
}

function handleXMLChange(dispatch, xml, exercise) {
  XMLParser.parseString(xml, (err, result) => {
    if(err || result === null) {
      console.dir(err);
    }
    else {
      dispatch(updateExerciseXML(exercise, xml));
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
    exerciseName: state.get('activeExercise'),
    exerciseState: activeExerciseState
  })
};

const mapDispatchToProps = dispatch => {
  return {
    onQuestionInputKeyUp: (event,exercise,question) => handleQuestionInputKeyUp(dispatch, event, exercise, question),
    onXMLChange: /*(xml, exercise) => handleXMLChange(dispatch, xml, exercise)*/ _.throttle((xml, exercise) => handleXMLChange(dispatch, xml, exercise), 1000),
    onSave: (exercise) => handleSave(dispatch, exercise),
    onReset: (exercise) => handleReset(dispatch, exercise)
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercise)
