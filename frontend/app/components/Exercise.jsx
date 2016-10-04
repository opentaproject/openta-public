"use strict";
import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import Question from './Question.jsx';
import Spinner from './Spinner.jsx';
import immutable from 'immutable';
import moment from 'moment';
import DOMPurify from 'dompurify';
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

  renderQuestion = (itemjson, json, meta, exerciseKey) => {
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

  renderExerciseText = (itemjson, json, meta, exerciseKey) => {
    var children = itemjson.get('$children$', immutable.List([]))
                    .map(child => this.dispatchElement(child, json, meta, exerciseKey)).toSeq();
    return (
      <div className="uk-clearfix">
      <div className="uk-align-medium-right">{children}</div>
      <span dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(itemjson.get('$'))}} />
      </div>
    );
  }

  renderFigure = (itemjson, json, meta, exerciseKey) => {
    return (
              <a href={'/exercise/' + exerciseKey + '/asset/' + itemjson.get('$')} data-uk-lightbox data-lightbox-type="image"><img style={{maxHeight: '100pt'}} src={'/exercise/' + this.props.exerciseKey + '/asset/' + itemjson.get('$')} alt=""/></a>
    );
  }

  renderName = (itemjson, json, meta, exerciseKey) => {
    var deadline_date = meta.get('deadline_date');
    var deadline_date_format = moment(deadline_date).format('D MMM');
    
    return (
          <div>
          <h1 className="uk-article-title">{itemjson.get('$')}
          { deadline_date && <div className="uk-badge uk-badge-warning">Deadline: {deadline_date_format}</div>}
          </h1>
          </div>
    );
  }

  dispatchElement = (element, json, meta, exerciseKey) => {
    var itemDispatch = {
      'exercisename': this.renderName,
      'exercisetext': this.renderExerciseText,
      'figure': this.renderFigure,
      'question': this.renderQuestion
    };
    if(element.get('#name') in itemDispatch)
      return itemDispatch[element.get('#name')](element, json, meta, exerciseKey);
    else
      return (<span/>);
  }

  render() {
    var key = this.props.exerciseKey;
    var state = this.props.exerciseState;
    var pendingState = this.props.pendingState;
    var json = state.get('json', immutable.Map({}));
    var meta = state.get('meta', immutable.Map({}));
    if(meta === null)meta = immutable.Map({});
    var items = json.getIn(['exercise','$children$'], immutable.List([]))
              .map( child => this.dispatchElement(child, json, meta, key) ).toSeq();
    var exerciseDOM = (
        <article className="uk-article uk-margin-top" ref="exercise" key={key}>
        { meta.get('image', false) && <ExerciseImageUpload/> }
          {items}
        </article>
    );

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
