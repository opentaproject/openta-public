/*
 * This is the presentational part of a question. It contains the javascript and html code that is shown in the front-end to the user.
 * It consists of a React component (see documentation on github for more details).
 */
"use strict"; // It is recommended to use strict javascript for easier debugging
import React, { PropTypes, Component } from 'react'; // React specific import

import { registerQuestionType } from './question_type_dispatch.js' // Register function used at the bottom of this file to let the system know of the question type
import Alert from '../Alert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import Badge from '../Badge.jsx'; // Another component useful for showing badges in the form of small colored boxes. See below for examples.

export default class QuestionCompareNumeric extends Component {
  static propTypes = {
    questionData: PropTypes.object, // Data from exercise XML file, i.e. whats inside the <question> tag
    questionState: PropTypes.object, // Current question state together with response data from server
    submitFunction: PropTypes.func, // Call this function to submit an answer to the server. The only parameter is the answer data which is unconstrained: It could be a simple string as below or a dictionary of values if more information needs to be conveyed.
    questionPending: PropTypes.bool, // Indicates when we are waiting for a server response
  }

  constructor(props) {
    super(props);
    this.state = {
      value: this.props.questionState.getIn(['answer'], '')
    };
  }

  handleChange = (event) => {
    this.setState({value: event.target.value});
  }

  renderAsciiMath = (asciitext) => {
    try {
      //Some initial parsing of commonly used patterns
      var re = /([a-zA-Z]+)([0-9]+)/g;
      var parsed = asciitext.replace(re, '$1_$2');
      return AMTparseAMtoTeX(parsed);
    }
    catch(e) {
      return "invalid math";
    }
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
  var lastAnswerRendered = this.renderAsciiMath(lastAnswer);
  var correct = state.getIn(['response','correct'], undefined); // Boolean indicating if the grader reported correct answer

  // Custom state data
  var latex = state.getIn(['response','latex'], ''); // Custom field containing the latex code obtained from SymPy.
  var error = state.getIn(['response','error']); // Custom field containing error information
  var status = state.getIn(['response','status'], 'none'); // Custom field containing the overall status of the answer, corresponds to the css class map inputClass above
  // HTML output defined as JSX code: Contains HTML entities with className instead of class and with javascript code within curly braces.
  // The styling classes are from UIKit, see getuikit.com for available elements.
  var response = "";
  var showprevious = false;
  if(this.state.value === lastAnswer && lastAnswer !== '') {
    if(correct)
       response = (<Alert message={"$" + this.renderAsciiMath(this.state.value) + "$" + " is correct!"} type="success" key="input" hasMath={true}/>);
    else
      response = (<Alert message={"$" + this.renderAsciiMath(this.state.value) + "$" + " is incorrect"} type="warning" key="input" hasMath={true}/>);
  } else if(this.state.value !== ''){
    response = (<Alert message={"$" + this.renderAsciiMath(this.state.value) + "$" } hasMath={true} key="input"/>);
    showprevious = true;
  }
  return (
        <div className="uk-container">
          <label className="uk-form-row uk-display-inline-block">{question.get('text','')}</label>
{ showprevious && (<Badge message={"$" + lastAnswerRendered + "$"} hasMath={true} className="uk-text-small uk-align-right uk-margin-bottom-remove"/>)}
          <div className="uk-form-icon uk-width-1-1">
          { !pending && <i className="uk-icon-pencil"/> }
          { pending && <i className="uk-icon-cog uk-icon-spin"/> }
            <input className={"uk-width-1-1 "} type="text" value={this.state.value} onChange={this.handleChange} onKeyUp={(event) => { if(event.keyCode === 13)submit(event.target.value) } }></input>
          </div>
        { error && <Alert message={error} type="error" key="err"/> }
        { response }
        </div>
  );
}
}

/*
        { !correct && lastAnswer !== '' && <Alert message={"$" + latex + "$" + " is incorrect"} type="warning" key="incorrect"/> }
        { correct && <Alert message={"$" + latex + "$" + " is correct!"} type="success" key="correct"/> }
*/
//Register the question component with the system
registerQuestionType('compareNumeric', QuestionCompareNumeric);
