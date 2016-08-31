/*
 * This is the presentational part of a question. It contains the javascript and html code that is shown in the front-end to the user.
 * It consists of a React component (see documentation on github for more details).
 */
"use strict"; // It is recommended to use strict javascript for easier debugging
import React, { PropTypes, Component } from 'react'; // React specific import

import { registerQuestionType } from './question_type_dispatch.js' // Register function used at the bottom of this file to let the system know of the question type
import Alert from '../Alert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.

/* Example of additional structure for presentation. This is a map of different css classes that will be used below together with the status parameter specified in the python __init__.py part of the question type. */
var inputClass = {
  error: 'uk-form-danger',
  correct: 'uk-form-success',
  incorrect: '',
  none: ''
};

export default class QuestionCompareNumeric extends Component {
  static propTypes = {
    questionData: PropTypes.object, // Data from exercise XML file, i.e. whats inside the <question> tag
    questionState: PropTypes.object, // Current question state together with response data from server
    submitFunction: PropTypes.func, // Call this function to submit an answer to the server. The only parameter is the answer data which is unconstrained: It could be a simple string as below or a dictionary of values if more information needs to be conveyed.
    questionPending: PropTypes.bool, // Indicates when we are waiting for a server response
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
  var lastAnswer = state.getIn(['answer'], ''); // Last saved answer in database, same format as passed to the submitFunction
  var correct = state.getIn(['response','correct'], undefined); // Boolean indicating if the grader reported correct answer

  // Custom state data
  var latex = state.getIn(['response','latex'], ''); // Custom field containing the latex code obtained from SymPy.
  var error = state.getIn(['response','error']); // Custom field containing error information
  var status = state.getIn(['response','status'], 'none'); // Custom field containing the overall status of the answer, corresponds to the css class map inputClass above
  // HTML output defined as JSX code: Contains HTML entities with className instead of class and with javascript code within curly braces.
  // The styling classes are from UIKit, see getuikit.com for available elements.
  return (
        <div className="uk-container">
          <label className="uk-form-row">{question.get('text','')}</label>
          <div className="uk-form-icon uk-width-1-1">
          { !pending && <i className="uk-icon-pencil"/> }
          { pending && <i className="uk-icon-cog uk-icon-spin"/> }
            <input className={"uk-width-1-1 " + inputClass[status]} type="text" defaultValue={lastAnswer} onKeyUp={(event) => { if(event.keyCode === 13)submit(event.target.value) } }></input>
          </div>
        { error && <Alert message={error} type="error" key="err"/> }
        { !correct && lastAnswer !== '' && <Alert message={"$" + latex + "$" + " is incorrect"} type="warning" key="incorrect"/> }
        { correct && <Alert message={"$" + latex + "$" + " is correct!"} type="success" key="correct"/> }
        </div>
  );
}
}

//Register the question component with the system
registerQuestionType('compareNumeric', QuestionCompareNumeric);
