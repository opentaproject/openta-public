import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import XMLEditor from './XMLEditor.jsx';
import xml2js from 'xml2js';
import _ from 'lodash';
import { 
  updateQuestionResponse, 
  updateActiveExerciseXML, 
  updateActiveExercise  
} from '../actions.js';

var XMLParser = new xml2js.Parser({trim:true});

class BaseExercise extends Component {
  constructor() {
    super();
  } 

  static propTypes = {
  exercisejson: PropTypes.object.isRequired,
  exerciseName: PropTypes.string.isRequired,
  onQuestionInputKeyUp: PropTypes.func,
  onXMLChange: PropTypes.func,
  exerciseState: PropTypes.object
};

  render() {
    var exercisejson = this.props.exercisejson;
    var exercisexml = _.get(this.props.exerciseState, "xml", '');
    var figure = this.props.exercisejson.problem ? exercisejson.problem.figure[0] : "";
    var name = this.props.exerciseName;
    var onQuestionInputKeyUp = this.props.onQuestionInputKeyUp;
    var questions = [];
    if(exercisejson.problem) {
      questions = exercisejson.problem.thecorrectanswer.map( (q, index) => {
        var alerts = _.get(this.props.exerciseState, 'question.' + index + '.alerts',[]);
          return (
          <div className="uk-panel uk-panel-box uk-margin-top uk-border-rounded" key={index}>
              <label className="uk-form-row">{q.$.question}</label>
              <div className="uk-form-icon uk-width-1-1">
                <i className="uk-icon-pencil"/>
                <input className="uk-width-1-1" type="text" onKeyUp={(event) => onQuestionInputKeyUp(Object.assign({}, event), name, index)}></input>
              </div>
              {alerts}
          </div>
      )} );
    }
    var exerciseDOM = (
        <ul className="uk-grid uk-grid-width-xlarge-1-2">
        <li key="exercise">
        <article className="uk-article uk-margin-top" ref="exercise" key={name}>
          <h1 className="uk-article-title">{exercisejson.problem ? exercisejson.problem.name : "No name"}</h1>
          <div className="uk-clearfix">
            <div className="uk-align-medium-right">
              <img style={{maxHeight: '100pt'}} src={'http://localhost:8000/exercise/' + name + '/asset/' + figure} alt=""/>
            </div>
            <span dangerouslySetInnerHTML={{__html: exercisejson.problem ? exercisejson.problem.question[0].text[0]._ : ""}} />
          </div>
          <hr className="uk-article-divider"/>
          <form className="uk-form">
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
    var data = new FormData();
    data.append('json', JSON.stringify(payload));
    var fetchconfig = {
      method: "POST",
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
  if(event.keyCode == 13)
    dispatch(checkQuestion(exercise, question, event.target.value));
}

function handleXMLChange(dispatch, xml, exercise) {
  XMLParser.parseString(xml, (err, result) => {
    if(err || result === null) {
      console.dir(err);
    }
    else {
      dispatch(updateActiveExerciseXML(exercise, xml));
      dispatch(updateActiveExercise(result));
    }
  });
}

const mapStateToProps = state => {
  var activeExerciseState = _.get(state.exerciseState, state.activeExercise, {});
  return (
  {
    exercisejson: state.activeExerciseJSON,
    exerciseName: state.activeExercise,
    exerciseState: activeExerciseState
  })
};

const mapDispatchToProps = dispatch => {
  return {
    onQuestionInputKeyUp: (event,exercise,question) => handleQuestionInputKeyUp(dispatch, event, exercise, question),
    onXMLChange: (xml, exercise) => handleXMLChange(dispatch, xml, exercise)//_.throttle((xml) => handleXMLChange(dispatch, xml), 500)
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercise)
