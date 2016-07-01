import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';

class BaseExercise extends Component {
  constructor() {
    super();
  } 

  static propTypes = {
  exercisejson: PropTypes.object.isRequired,
  exerciseName: PropTypes.string.isRequired,
  onQuestionInputKeyUp: PropTypes.func
};

  //const BaseExercise = ({ exercisejson }) => (
  render() {
    var exercisejson = this.props.exercisejson;
    var figure = this.props.exercisejson.problem ? exercisejson.problem.figure[0] : "";
    var name = this.props.exerciseName;
    var onQuestionInputKeyUp = this.props.onQuestionInputKeyUp;
    var questions = [];
    if(exercisejson.problem) {
      questions = exercisejson.problem.thecorrectanswer.map( (q, index) => (
          <div className="uk-panel uk-panel-box uk-margin-top uk-border-rounded">
              <label className="uk-form-row">{q.$.question}</label>
              <div className="uk-form-icon uk-width-1-1">
                <i className="uk-icon-pencil"/>
                <input className="uk-width-1-1" type="text" onKeyUp={(event) => onQuestionInputKeyUp(Object.assign({}, event), name, index)}></input>
              </div>
          </div>
      ) );
    }
    return (
      <div className="uk-width-medium-3-4 uk-margin-top">
        <article className="uk-article uk-width-medium-3-4" ref="exercise">
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

//BaseExercise.propTypes = {
//  exercisejson: PropTypes.object.isRequired
//};

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
    .then(res => console.dir(res));
    return "True";
  }
}

function handleQuestionInputKeyUp(dispatch, event, exercise, question) {
  console.dir([event, exercise, question]);
  dispatch(checkQuestion(exercise, question, event.target.value));
}

const mapStateToProps = state => (
  {
    exercisejson: state.activeExerciseJSON,
    exerciseName: state.activeExercise
  });

const mapDispatchToProps = dispatch => {
  return {
    onQuestionInputKeyUp: (event,exercise,question) => handleQuestionInputKeyUp(dispatch, event, exercise, question)
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercise)
