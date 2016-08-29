"use strict";
import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import Question from './Question.jsx';
import immutable from 'immutable';

import { 
  updateExerciseXML, 
  updateExerciseJSON,
  setExerciseModifiedState
} from '../actions.js';
import {
  saveExercise,
  fetchExercise,
  checkQuestion
} from '../fetchers.js';

class BaseExercise extends Component {
  constructor() {
    super();
  } 

  static propTypes = {
  exerciseKey: PropTypes.string.isRequired,
  onQuestionInputKeyUp: PropTypes.func,
  exerciseState: PropTypes.object
};

  render() {
    var key = this.props.exerciseKey;
    var state = this.props.exerciseState;
    var json = state.get('json', immutable.Map({}));
    var figure = json.getIn(['exercise', 'figure', '$']);
    var questions = json.getIn(['exercise', 'question'], immutable.List([]));
    var questionsDOMArray = questions.map( question => (
          <form key={question.get('@key')} className="uk-form" onSubmit={(event) => event.preventDefault()}>
            <Question exerciseKey={key} questionKey={question.get('@key')}/>
          </form>
    ));

    var exerciseDOM = (
        <article className="uk-article uk-margin-top" ref="exercise" key={key}>
          <div className="uk-grid">
          <h1 className="uk-article-title">{json.getIn(['exercise','name','$'])}</h1>
          </div>
          <div className="uk-clearfix">
            <div className="uk-align-medium-right">
            { figure && <img style={{maxHeight: '100pt'}} src={'/exercise/' + key + '/asset/' + figure} alt=""/> }
            </div>
            <span dangerouslySetInnerHTML={{__html: json.getIn(['exercise','text','$'])}} />
          </div>
          <hr className="uk-article-divider"/>
          { questionsDOMArray }
        </article>
    );

    return exerciseDOM;
  }

  componentDidUpdate(props,state,root) {
    var node = ReactDOM.findDOMNode(this.refs.exercise);
    MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
  }
}

const mapStateToProps = state => {
  //var activeExerciseState = _.get(state.exerciseState, state.activeExercise, {});
  var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));
  return (
  {
    exerciseKey: state.get('activeExercise'),
    exerciseState: activeExerciseState
  })
};

const mapDispatchToProps = dispatch => {
  return {
    onQuestionInputKeyUp: (event,exercise,question) => handleQuestionInputKeyUp(dispatch, event, exercise, question),
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercise)
