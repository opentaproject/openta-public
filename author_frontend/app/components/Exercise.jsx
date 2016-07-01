import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';

class BaseExercise extends Component {
  constructor() {
    super();
  } 

  static propTypes = {
  exercisejson: PropTypes.object.isRequired,
  exerciseName: PropTypes.string.isRequired
};

  //const BaseExercise = ({ exercisejson }) => (
  render() {
    var exercisejson = this.props.exercisejson;
    var figure = this.props.exercisejson.problem ? exercisejson.problem.figure[0] : "";
    var name = this.props.exerciseName;
    var questions = [];
    if(exercisejson.problem) {
      questions = exercisejson.problem.thecorrectanswer.map( q => (
          <div className="uk-panel uk-panel-box uk-margin-top uk-border-rounded">
              <label className="uk-form-row">{q.$.question}</label>
              <div className="uk-form-icon uk-width-1-1">
                <i className="uk-icon-pencil"/>
                <input className="uk-width-1-1" type="text"></input>
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
              <img style={{maxHeight: '100pt'}} src={'http://localhost:8000/exercise/' + name + '/' + figure} alt=""/>
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

//BaseExercise.componentDidMount = root => MathJax.Hub.Queue(["Typeset", MathJax.Hub, root]);
//BaseExercise.componentDidMount = root => console.log("Mounted");

const mapStateToProps = state => (
  {
    exercisejson: state.activeExerciseJSON,
    exerciseName: state.activeExercise
  });

export default connect(mapStateToProps)(BaseExercise)
