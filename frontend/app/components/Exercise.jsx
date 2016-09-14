"use strict";
import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import Question from './Question.jsx';
import Spinner from './Spinner.jsx';
import immutable from 'immutable';
import ExerciseImageUpload from './ExerciseImageUpload.jsx';

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
    admin: PropTypes.bool,
  exerciseKey: PropTypes.string.isRequired,
  onQuestionInputKeyUp: PropTypes.func,
  exerciseState: PropTypes.object,
  pendingState: PropTypes.object
};

  renderQuestion = (itemjson, json, exerciseKey) => {
    var questions = json.getIn(['exercise', 'question'], immutable.List([]));
    var question = itemjson;
    return (
          <div>
          { questions.filter( q => q.getIn(['@attr','key']) == question.getIn(['@attr','key']) ).count() > 1 && this.props.admin && <Alert message="Duplicate question keys! (If you copied a question please change the key attribute)" type="error"/> } 
          <form key={question.getIn(['@attr','key'])} className="uk-form" onSubmit={(event) => event.preventDefault()}>
            <Question exerciseKey={exerciseKey} questionKey={question.getIn(['@attr','key'])}/>
          </form>
          </div>
    );
  }

  renderExerciseText = (itemjson, json, exerciseKey) => {
    var children = itemjson.get('$children$', immutable.List([]))
                    .map(child => this.dispatchElement(child, json, exerciseKey)).toSeq();
    return (
      <div className="uk-clearfix">
      <div className="uk-align-medium-right">{children}</div>
      <span dangerouslySetInnerHTML={{__html: itemjson.get('$')}} />
      </div>
    );
  }

  renderFigure = (itemjson, json, exerciseKey) => {
    return (
              <img style={{maxHeight: '100pt'}} src={'/exercise/' + this.props.exerciseKey + '/asset/' + itemjson.get('$')} alt=""/>
    );
    //return (
    //        <div className="uk-align-medium-right">
    //          <img style={{maxHeight: '100pt'}} src={'/exercise/' + this.props.exerciseKey + '/asset/' + itemjson.get('$')} alt=""/>
    //        </div>
    //);
  }

  renderName = (itemjson, json, exerciseKey) => {
    return (
          <h1 className="uk-article-title">{itemjson.get('$')}</h1>
    );
  }

  dispatchElement = (element, json, exerciseKey) => {
    var itemDispatch = {
      'exercisename': this.renderName,
      'exercisetext': this.renderExerciseText,
      'figure': this.renderFigure,
      'question': this.renderQuestion
    };
    if(element.get('#name') in itemDispatch)
      return itemDispatch[element.get('#name')](element, json, exerciseKey);
    else
      return (<span/>);
  }

  render() {
    var key = this.props.exerciseKey;
    var state = this.props.exerciseState;
    var pendingState = this.props.pendingState;
    var json = state.get('json', immutable.Map({}));
    //var figure = json.getIn(['exercise', 'figure', '$']);
    //var questions = json.getIn(['exercise', 'question'], immutable.List([]));
    var items = json.getIn(['exercise','$children$'], immutable.List([]))
              .map( child => this.dispatchElement(child, json, key) ).toSeq();
    var exerciseDOM = (
        <article className="uk-article uk-margin-top" ref="exercise" key={key}>
        <ExerciseImageUpload/>
          {items}
        </article>
    );
//    var questionsDOMArray = questions.map( question => (
//          <div>
//          { questions.filter( q => q.getIn(['@attr','key']) == question.getIn(['@attr','key']) ).count() > 1 && this.props.admin && <Alert message="Duplicate question keys! (If you copied a question please change the key attribute)" type="error"/> } 
//          <form key={question.getIn(['@attr','key'])} className="uk-form" onSubmit={(event) => event.preventDefault()}>
//            <Question exerciseKey={key} questionKey={question.getIn(['@attr','key'])}/>
//          </form>
//          </div>
//    ));
//
//    var exerciseDOM = (
//        <article className="uk-article uk-margin-top" ref="exercise" key={key}>
//          <div className="uk-grid">
//          <h1 className="uk-article-title">{json.getIn(['exercise','exercisename','$'])}</h1>
//          </div>
//          <div className="uk-clearfix">
//            <div className="uk-align-medium-right">
//            { figure && <img style={{maxHeight: '100pt'}} src={'/exercise/' + key + '/asset/' + figure} alt=""/> }
//            </div>
//            <span dangerouslySetInnerHTML={{__html: json.getIn(['exercise','exercisetext','$'])}} />
//          </div>
//          { /* <hr className="uk-article-divider"/> */ }
//          { questionsDOMArray }
//        </article>
//    );

    if(pendingState.getIn(['exercises', key, 'loadingJSON'], false)) {
      return (<Spinner/>);
    }
    else 
      return exerciseDOM;
  }

  componentDidUpdate(props,state,root) {
    var node = ReactDOM.findDOMNode(this.refs.exercise);
    //MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
    if(node !== null)
      renderMathInElement(node, {
        delimiters: [{left: "$", right: "$", display: false}]
      });
  }
}

const mapStateToProps = state => {
  //var activeExerciseState = _.get(state.exerciseState, state.activeExercise, {});
  var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));
  return (
  {
    admin: state.getIn(['login', 'admin']),
    exerciseKey: state.get('activeExercise'),
    exerciseState: activeExerciseState,
    pendingState: state.get('pendingState')
  })
};

const mapDispatchToProps = dispatch => {
  return {
    onQuestionInputKeyUp: (event,exercise,question) => handleQuestionInputKeyUp(dispatch, event, exercise, question),
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercise)
