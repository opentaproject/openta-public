import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
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

class BaseExercise extends Component {
  constructor() {
    super();
  } 

  static propTypes = {
  exerciseName: PropTypes.string.isRequired,
  onQuestionInputKeyUp: PropTypes.func,
  //onSave: PropTypes.func,
  //onReset: PropTypes.func,
  //onXMLChange: PropTypes.func,
  exerciseState: PropTypes.object
};

  render() {
    var exerciseState = this.props.exerciseState;
    var exercisejson = exerciseState.get('json', immutable.Map({}) );
    //var exercisexml = exerciseState.get('xml','');//_.get(this.props.exerciseState, "xml", '');
    var figure = exercisejson.getIn(['problem','figure','$']);//this.props.exercisejson.problem ? exercisejson.problem.figure[0] : "";
    var name = this.props.exerciseName;
    var renderName = exercisejson.getIn(['problem','name','$'], "No name");
    var renderText = exercisejson.getIn(['problem','question','text','$'], "");
    var onQuestionInputKeyUp = this.props.onQuestionInputKeyUp;
    //var onSave = this.props.onSave;
    //var onReset = this.props.onReset;
    //var savePending = exerciseState.get('savepending');
    //var saveError = exerciseState.get('saveerror');
    //var resetPending = exerciseState.get('resetpending');
    //var modified = exerciseState.get('modified');
    var questions = [];
    if(exercisejson.has('problem')) {
      questions = exercisejson.getIn(['problem','thecorrectanswer'],{}).rest().map( (q, index_) => {
        var index = index_ + 1;
        var alerts = exerciseState.getIn(['question',index.toString(),'alerts'],immutable.List([])).toList()
          .map( (alert, alertindex) => (<Alert message={alert.get('message')} type={alert.get('type')} key={alertindex}/>) );
        var status = exerciseState.getIn(['question', index.toString(), 'status'], 'none');
        var inputClass = {
          error: 'uk-form-danger',
          correct: 'uk-form-success',
          incorrect: '',
          none: ''
        };
        return (
          <div>
          <div className="uk-panel uk-panel-box uk-margin-top" key={index}>
          {/*<div className="uk-panel uk-panel-box uk-panel-box-primary uk-margin-top uk-border-rounded" key={index}>*/}
              <div className="uk-container">
              <label className="uk-form-row">{q.getIn(['@question'],'')}</label>
              <div className="uk-form-icon uk-width-1-1">
                <i className="uk-icon-pencil"/>
                <input className={"uk-width-1-1 " + inputClass[status]} type="text" onKeyUp={(event) => onQuestionInputKeyUp(Object.assign({}, event), name, index)}></input>
              </div>
              {alerts}
              </div>
          </div>
          </div>
      )
      } );
    }
    var exerciseDOM = (
        <article className="uk-article uk-margin-top" ref="exercise" key={name}>
          <div className="uk-grid">
          <h1 className="uk-article-title">{renderName}</h1>
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
    );
    return (
      <div>
      {name ? exerciseDOM : ""}
      </div>
    );
    /*(
      <div className="uk-width-medium-5-6">
      {name ? exerciseDOM : ""}
      </div>*/
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
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercise)
