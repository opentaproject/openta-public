import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import _ from 'lodash';

class BaseExercise extends Component {
  constructor() {
    super();
  } 

  static propTypes = {
  exercisejson: PropTypes.object.isRequired,
  exerciseName: PropTypes.string.isRequired,
  onQuestionInputKeyUp: PropTypes.func,
  exerciseState: PropTypes.object
};

  render() {
    var exercisejson = this.props.exercisejson;
    var figure = this.props.exercisejson.problem ? exercisejson.problem.figure[0] : "";
    var name = this.props.exerciseName;
    var onQuestionInputKeyUp = this.props.onQuestionInputKeyUp;
    var questions = [];
    if(exercisejson.problem) {
      questions = exercisejson.problem.thecorrectanswer.map( (q, index) => {
        var alerts = _.get(this.props.exerciseState, 'question.' + index + '.alerts',[]);
          return (
          <div className="uk-panel uk-panel-box uk-margin-top uk-border-rounded">
              <label className="uk-form-row">{q.$.question}</label>
              <div className="uk-form-icon uk-width-1-1">
                <i className="uk-icon-pencil"/>
                <input className="uk-width-1-1" type="text" onKeyUp={(event) => onQuestionInputKeyUp(Object.assign({}, event), name, index)}></input>
              </div>
              {alerts}
          </div>
      )} );
    }
    return (
      <div className="uk-width-medium-3-4 uk-margin-top">
        <article className="uk-article uk-width-medium-3-4" ref="exercise" key={name}>
          <h1 className="uk-article-title">{exercisejson.problem ? exercisejson.problem.name : "No name"}</h1>
          <div className="uk-clearfix">
            <div className="uk-align-medium-right uk-width-medium-2-4">
              <img style={{maxHeight: '100pt'}} src={'http://localhost:8000/exercise/' + name + '/asset/' + figure} alt=""/>
            </div>
            <span dangerouslySetInnerHTML={{__html: exercisejson.problem ? exercisejson.problem.question[0].text[0]._ : ""}} />
          </div>
          <hr className="uk-article-divider"/>
          <form className="uk-form">
          {questions}
          </form>
        </article>
      </div>
    );
  }

  componentDidUpdate(props,state,root) {
    var node = ReactDOM.findDOMNode(this.refs.exercise);
    MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
  }
}

function updateQuestionResponse(exercise, question, response) {
  var alerts = []
  if(response.error) {
    alerts.push( ( <Alert message={response.error} type="error"/> )
               );
  }
  if(response.correct !== undefined) {
    if(response.correct) {
      var message = '$' + _.get(response, 'latex', '') + '$' + " is correct!";
      alerts.push( (<Alert message={message} type="success"/>) );
    } else {
      var message = '$' + _.get(response, 'latex', '') + '$' + " is incorrect.";
      alerts.push( (<Alert message={message} type="warning"/> ) );
    }
  }
  var data = { 
    exerciseState: { 
      [exercise]: {
        question: {
         [question]: {
           alerts: alerts
         }
        }
      }
    }
  }; 
  return {
    type: 'UPDATE_QUESTION_RESPONSE',
    exercise: exercise,
    question: question,
    data: data
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
    onQuestionInputKeyUp: (event,exercise,question) => handleQuestionInputKeyUp(dispatch, event, exercise, question)
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercise)
