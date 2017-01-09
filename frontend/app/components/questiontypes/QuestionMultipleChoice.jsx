/*
 * This is the presentational part of a question. It contains the javascript and html code that is shown in the front-end to the user.
 * It consists of a React component (see documentation on github for more details).
 */
"use strict"; // It is recommended to use strict javascript for easier debugging
import React, { PropTypes, Component } from 'react'; // React specific import

import { registerQuestionType } from './question_type_dispatch.js' // Register function used at the bottom of this file to let the system know of the question type
import Alert from '../Alert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import SafeMathAlert from '../SafeMathAlert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import Badge from '../Badge.jsx'; // Another component useful for showing badges in the form of small colored boxes. See below for examples.
import MathSpan from '../MathSpan.jsx';
import immutable from 'immutable';
import {SUBPATH} from '../../settings.js';
import DOMPurify from 'dompurify';

export default class QuestionMultipleChoice extends Component {
  static propTypes = {
    questionData: PropTypes.object, // Data from exercise XML file, i.e. whats inside the <question> tag
    questionState: PropTypes.object, // Current question state together with response data from server
    submitFunction: PropTypes.func, // Call this function to submit an answer to the server. The only parameter is the answer data which is unconstrained: It could be a simple string as below or a dictionary of values if more information needs to be conveyed.
    questionPending: PropTypes.bool, // Indicates when we are waiting for a server response
    isAuthor: PropTypes.bool, //Indicates if user is an author/content creator.
    canViewSolution: PropTypes.bool, //Indicates if user is allowed to see solution.
    exerciseKey: PropTypes.string, //Exercise key
  }

  constructor(props) {
    super(props);
    this.state = {
      choice: undefined
    }
  }

  changeChoice = (choice) => {
    this.setState({choice: choice});
    this.props.submitFunction(choice);
  }

  renderText = (itemjson) => {
    var children = itemjson.get('$children$', immutable.List([]))
                    .map(child => this.dispatchElement(child)).toSeq();
    return (
      <div className="uk-clearfix" key={"text" + itemjson.get('$')}>
      <div className="uk-align-medium-right">{children}</div>
      <span dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(itemjson.get('$'))}} />
      </div>
    );
  }

  renderFigure = (itemjson) => {
    return (
              <a key={"figure"+itemjson.get('$')} href={SUBPATH + '/exercise/' + this.props.exerciseKey + '/asset/' + itemjson.get('$')} data-uk-lightbox data-lightbox-type="image"><img style={{maxHeight: '100pt'}} src={SUBPATH + '/exercise/' + this.props.exerciseKey + '/asset/' + itemjson.get('$')} alt=""/></a>
    );
  }
  renderAsset = (itemjson) => {
    return (
      <a key={"asset" + itemjson.get('$')} className="uk-button uk-button-small" href={SUBPATH + '/exercise/' + this.props.exerciseKey + '/asset/' + itemjson.get('$')}>{itemjson.getIn(['@attr', 'name'])}</a>
    );
  }

  dispatchElement = (element) => {
    var itemDispatch = {
      'text': this.renderText,
      'figure': this.renderFigure,
      'asset': this.renderAsset,
    };
    if(element.get('#name') in itemDispatch)
      return itemDispatch[element.get('#name')](element);
    else
      return null;
  }

  renderContentInPanel = (element, badge) => {
    var children = element.get('$children$', immutable.List([]))
              .map( child => this.dispatchElement(child) ).toSeq();
    return (
      <div className="uk-panel uk-panel-box">
        <div className="uk-panel-badge">
          {badge}
        </div>
        {children}
        <MathSpan>{element.get('$')}</MathSpan>
      </div>
    )
  }

  /* render gets called every time the question is shown on screen */
  render() {  
  // Some convenience definitions
  var question = this.props.questionData;
  var state = this.props.questionState;
  var submit = this.props.submitFunction;
  var pending = this.props.questionPending;
  
  /* Both the questionData and questionState are of type Map from immutable.js. They are nested dictionaries that are accessed via the get and getIn functions. For example question.get('text') retrieves <question> <text> * </text> </question>. Deeper structures can be accessed with getIn, for example question.getIn(['tag1', 'tag2']) would retrieve <question> <tag1> <tag2> * </tag2> </tag1> </question>. */

  // System state data
  var lastAnswer = parseInt(state.getIn(['answer'], '')); // Last saved answer in database, same format as passed to the submitFunction
  var correct = state.getIn(['response','correct'])/*, false) || state.getIn(['correct'], false);*/ // Boolean indicating if the grader reported correct answer
  var choicesElements = question.get('choice',immutable.List([]));
  if( !immutable.List.isList(choicesElements) )choicesElements = immutable.List([choicesElements]);
  var choices = choicesElements.map( (item, key) => {
    var style = {}
    var divClass = key === this.state.choice ? 'uk-panel-box-primary' : '';
    if(correct && key === lastAnswer)style = {backgroundColor: '#f2fae3'}
    if(!correct && key === lastAnswer)style = {backgroundColor: '#fff1f0'}
    var children = item.get('$children$', immutable.List([]))
              .map( child => this.dispatchElement(child) ).toSeq();
    return (
    <div className="uk-width-1-1" key={key}>
      <div style={style} className={"uk-panel uk-panel-box uk-margin-top pointer " + divClass} onClick={() => this.changeChoice(key)}>
        <div className="uk-panel-badge">
        { this.props.canViewSolution && key === parseInt(question.getIn(['correct','$'], -1))-1 && <div className="uk-margin-small-right uk-badge uk-badge-success">correct</div> }
        { this.props.isAuthor && <div className="uk-badge">{key+1}</div> }
        </div>
        <MathSpan>{item.get('$')}</MathSpan>
        {children}
      </div>
    </div>
  )}
                                          );

  // Custom state data
  var error = state.getIn(['response','error']); // Custom field containing error information
  var author_error = state.getIn(['response','author_error']); // Custom field containing error information
  return (
        <div className="">
          <label className="uk-form-row uk-display-inline-block uk-margin-bottom">{question.getIn(['text','$'],'')} </label>
          { question.has('hint') && !correct && state.get('answer') !== '' && this.renderContentInPanel(question.get('hint'), (<div className="uk-badge">Hint</div>)) }
          <div className="uk-grid uk-grid-small">
              {choices}
          </div>
          { error && <Alert message={error} type="error" key="err"/> }
          { author_error && this.props.isAuthor && <Alert message={author_error} type="error" key="author_error"/> }
        </div>
  );
}
}

//Register the question component with the system
registerQuestionType('multipleChoice', QuestionMultipleChoice);
