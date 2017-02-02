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
import {SUBPATH} from '../settings.js';

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

var unstableKey = 0;
const nextUnstableKey = () => unstableKey++;

class BaseExercise extends Component {
  constructor() {
    super();
    this.itemDispatch = {
      'exercisename': this.renderName,
      'text': this.renderText,
      'figure': this.renderFigure,
      'question': this.renderQuestion,
      'solution': this.renderSolution,
      'asset': this.renderAsset,
      'p': this.renderHTMLElement(),
      'i': this.renderHTMLElement(),
      'b': this.renderHTMLElement(),
      'strong': this.renderHTMLElement(),
      'em': this.renderHTMLElement(),
      'h3': this.renderHTMLElement(),
      'h2': this.renderHTMLElement(),
      'h1': this.renderHTMLElement(),
      'ul': this.renderHTMLElement("uk-list"),
      'li': this.renderHTMLElement(),
      'right': this.renderRight,
      '__text__': this.renderBareText,
    };
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
          <div key={"q" + question.getIn(['@attr', 'key'])}>
          { questions.filter( q => q.getIn(['@attr','key']) == question.getIn(['@attr','key']) ).count() > 1 && this.props.admin && <Alert message="Duplicate question keys! (If you copied a question please change the key attribute)" type="error"/> } 
          <form key={question.getIn(['@attr','key'])} className="uk-form" onSubmit={(event) => event.preventDefault()}>
          {<Question exerciseKey={exerciseKey} questionKey={question.getIn(['@attr','key'])}/>}
          </form>
          </div>
    );
  }


  renderLegacyText = (itemjson, json, meta, exerciseKey) => {
    var children = itemjson.get('$children$', immutable.List([]))
                    .filter(item => item.get('#name') === 'figure')
                    .map(child => this.dispatchElement(child, json, meta, exerciseKey)).toSeq();
    return (
      <div className="uk-clearfix" key={"text"}>
      <div className="uk-align-medium-right">{children}</div>
      <span dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(itemjson.get('$'))}} />
      </div>
    );
  }

  renderText = (itemjson, json, meta, exerciseKey) => {
    var childrenList = itemjson.get('$children$', immutable.List([]));

    if(childrenList.filter( item => item.get('#name','') === 'figure').size == 1 &&
        childrenList.size == 2)
      return this.renderLegacyText(itemjson, json, meta, exerciseKey);
    var children =  childrenList 
                    .map(child => this.dispatchElement(child, json, meta, exerciseKey)).toSeq();
    return (
      <div className="uk-clearfix" key={"text" + nextUnstableKey()}>
        {children} 
      </div>
    );
  }

  renderFigure = (itemjson, json, meta, exerciseKey) => {
    return (
              <a className="uk-thumbnail uk-thumbnail-small" key={"figure"+itemjson.get('$')} href={SUBPATH + '/exercise/' + exerciseKey + '/asset/' + itemjson.get('$').trim()} data-uk-lightbox data-lightbox-type="image">
                <img src={SUBPATH + '/exercise/' + this.props.exerciseKey + '/asset/' + itemjson.get('$','').trim()} alt=""/>
                { itemjson.has('caption') && <div className="uk-thumbnail-caption">{itemjson.getIn(['caption', '$'])}</div> }
              </a>
    );
  }

  renderSolution = (itemjson, json, meta, exerciseKey) => {
    var children = itemjson.get('$children$', immutable.List([]))
                    .map(child => this.dispatchElement(child, json, meta, exerciseKey)).toSeq();
    return (
      <div className="uk-margin-bottom uk-text-center" key={"solution"}>
      { meta.get('solution', false) && children }

      {!meta.get('solution', false) && this.props.view && <div className="uk-block uk-block-muted uk-padding-remove uk-text-warning">Dold för studenter. {this.props.author && <span>Visa för studenter genom att klicka i "solution" i inställningarna.</span>}</div> }
      {!meta.get('solution', false) && this.props.view && <div className="uk-block uk-block-muted uk-padding-remove">{children}</div>}
      </div>
    );
  }

  renderAsset = (itemjson, json, meta, exerciseKey) => {
    return (
      <a key={"asset" + itemjson.get('$')} className="uk-button uk-button-small" href={SUBPATH + '/exercise/' + exerciseKey + '/asset/' + itemjson.get('$')}>{itemjson.getIn(['@attr', 'name'])}</a>
    );
  }

  renderName = (itemjson, json, meta, exerciseKey) => {
    var deadlineDate = meta.get('deadline_date');
    if(deadlineDate) {
      var deadlineTime = meta.get('deadline_time');
      var deadlineDateFormat = moment(deadlineDate + ' ' + deadlineTime).format('D MMM HH:mm');
    }
    var obligatorisk = meta.get('required', false);
    var bonus = meta.get('bonus', false);
    
    return (
          <div key="name">
          <h1 className="uk-article-title">{itemjson.get('$')}
          { deadlineDate && <div className="uk-badge uk-badge-danger">
            <a data-uk-tooltip title="Du kan fortfarande kontrollera svar efter deadline men de kommer inte räknas mot obligatorisk/bonus.">
            Deadline: {deadlineDateFormat}
            <i className="uk-icon uk-icon-small uk-icon-question-circle-o uk-margin-small-left"/></a>
            </div>}
          { deadlineDate && obligatorisk && <div className="uk-badge uk-margin-small-left">Obligatorisk</div>}
          { deadlineDate && bonus && <div className="uk-badge uk-badge-warning uk-margin-small-left">Bonus</div>}
          </h1>
          </div>
    );
  }

  renderHTMLElement = (className="") => (itemjson, json, meta, exerciseKey) => {
    var children = itemjson.get('$children$', immutable.List([]))
    .map(child => this.dispatchElement(child, json, meta, exerciseKey)).toList();
    var itemDOM = React.createElement(itemjson.get('#name'), {
      className: className + " " + itemjson.getIn(['@attr', 'class']),
      style: itemjson.getIn(['@attr', 'style']),
      key: nextUnstableKey(),
    }, children);
    return itemDOM;
  }

  renderBareText = (itemjson, json, meta, exerciseKey) => (<span key={nextUnstableKey()} dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(itemjson.get('$'))}}/>)

  renderRight = (itemjson, json, meta, exerciseKey) => (
    <div className="uk-align-medium-right" key={nextUnstableKey()}>
      {
        itemjson.get('$children$', immutable.List([]))
          .map(child => this.dispatchElement(child, json, meta, exerciseKey)).toList()
      }
    </div>)

  dispatchElement = (element, json, meta, exerciseKey) => {
    if(element.get('#name') in this.itemDispatch)
      return this.itemDispatch[element.get('#name')](element, json, meta, exerciseKey);
    else
      return null;
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
        <article className="uk-article uk-margin-top uk-margin-small-right uk-margin-small-left" ref="exercise" key={key}>
        { meta.get('image', false) && <div className="uk-float-right uk-margin-small-right"><ExerciseImageUpload/></div> }
          {items}
        </article>
    );

    if(pendingState.getIn(['exercises', key, 'loadingJSON'], false)) {
      return (<Spinner/>);
    }
    else 
      return exerciseDOM;
  }

  componentDidMount(props, state, root) {
    this.componentDidUpdate(props, state, root);
  }
  componentDidUpdate(props,state,root) {
    var node = ReactDOM.findDOMNode(this.refs.exercise);
    //MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
    if(node !== null)
      renderMathInElement(node, {
        delimiters: [
          {left: "$", right: "$", display: false},
          {left: "\\[", right: "\\]", display: true}
        ]
      });
  }
}

const mapStateToProps = state => {
  var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));
  return (
  {
    author: state.getIn(['login', 'groups'],immutable.List([])).includes('Author'),
    admin: state.getIn(['login', 'groups'],immutable.List([])).includes('Admin'),
    view: state.getIn(['login', 'groups'],immutable.List([])).includes('View'),
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
