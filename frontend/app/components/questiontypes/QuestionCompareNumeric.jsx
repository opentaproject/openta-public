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
import HelpCompareNumeric from './HelpCompareNumeric.jsx';
import mathjs from 'mathjs';

export default class QuestionCompareNumeric extends Component {
  static propTypes = {
    questionData: PropTypes.object, // Data from exercise XML file, i.e. whats inside the <question> tag
    questionState: PropTypes.object, // Current question state together with response data from server
    submitFunction: PropTypes.func, // Call this function to submit an answer to the server. The only parameter is the answer data which is unconstrained: It could be a simple string as below or a dictionary of values if more information needs to be conveyed.
    questionPending: PropTypes.bool, // Indicates when we are waiting for a server response
    isAuthor: PropTypes.bool, //Indicates if user is an author/content creator.
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

  componentWillReceiveProps = (newProps) => {
    //this.setState({ value: newProps.questionState.getIn(['answer'],'') });
  }

  componentWillMount = () => {
    var vars = this.parseVariables(this.props.questionData.getIn(['global','$'], ''));
    if(vars) {
      vars.map( v => {
        if(AMsymbols.find( item => item.input === v ) === undefined)
          newsymbol({input:v,  tag:"mi", output: v, tex: v, ttype:0, val: true});
      });
    }
  }

  renderAsciiMath = (asciitext) => {
    try {
      //Some initial parsing of commonly used patterns
      var re = /([a-zA-Z]+)([0-9]+)/g;
      var parsed = asciitext.replace(re, '$1_$2');
      return AMTparseAMtoTeX(parsed);
    }
    catch(e) {
      console.dir(e);
      return "invalid math";
    }
  }

  parseVariables = (variableString) => {
    var vars = variableString.trim()
      .split(';')
      .filter(str => str !== "")
      .map( str => str.split('=') )
      .map( entry => entry[0].trim() );
      return vars;
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
  var correct = state.getIn(['response','correct'], false) || state.getIn(['correct'], false); // Boolean indicating if the grader reported correct answer

  // Custom state data
  var latex = state.getIn(['response','latex'], ''); // Custom field containing the latex code obtained from SymPy.
  var error = state.getIn(['response','error']); // Custom field containing error information
  var warning = state.getIn(['response','warning']); // Custom field containing error information
  var status = state.getIn(['response','status'], 'none'); // Custom field containing the overall status of the answer, corresponds to the css class map inputClass above
  var varsList = this.parseVariables(this.props.questionData.getIn(['global','$'], ''));
  var vars = {}
  if(varsList) {
    varsList.map( v => {vars[v] = 1;} );
  }
  var availableVariables = varsList.length ? "(i termer av " + varsList.join(", ") + ")" : "";
  // HTML output defined as JSX code: Contains HTML entities with className instead of class and with javascript code within curly braces.
  // The styling classes are from UIKit, see getuikit.com for available elements.
  var graderResponse = null;
  var input = this.state.value.trim();
  var hasChanged = input !== lastAnswer;
  var nonEmpty = input !== "";
  if(input === lastAnswer && lastAnswer !== '' && !error) {
    if(correct)
       graderResponse = (<Alert message={"$" + this.renderAsciiMath(input) + "$" + " är korrekt."} type="success" key="input" hasMath={true}/>);
    else
      graderResponse = (<Alert message={"$" + this.renderAsciiMath(input) + "$" + " är inte korrekt."} type="warning" key="input" hasMath={true}/>);
  } else if(input !== ''){
    graderResponse = (<SafeMathAlert message={this.renderAsciiMath(input)} key="input"/>);
  }
  var mathjsError = null;
  try {
    var mathjsParse = mathjs.eval(input, vars);
  }
  catch(e) {
    if(e instanceof SyntaxError)
      mathjsError = (<Alert type="warning" message={ e.toString() }/>);
  }
  return (
        <div className="">
          <label className="uk-form-row uk-display-inline-block">{question.getIn(['text','$'],'')} <span className="uk-text-small uk-text-primary">{availableVariables}</span><HelpCompareNumeric/></label>
{ hasChanged && (<Badge message={"previous: " + lastAnswer} hasMath={false} className="uk-text-small uk-margin-small-left uk-margin-bottom-remove"/>)}
          <div className="uk-grid uk-grid-small">
          <div className="uk-width-5-6">
          <div className="uk-form-icon uk-width-1-1">
          { !pending && <i className="uk-icon-pencil"/> }
          { pending && <i className="uk-icon-cog uk-icon-spin"/> }
            <input className={"uk-width-1-1 "} type="text" value={this.state.value} onChange={this.handleChange} ></input>
          </div>
          </div>
          <div className="uk-width-1-6">
            <a onClick={(event) => submit(input)} className={ "uk-width-1-1 uk-button uk-padding-remove " + (nonEmpty && hasChanged && !mathjsError ? "uk-button-success" : "")}>
              { pending && <i className="uk-icon-cog uk-icon-spin"/> }
              { !pending && <i className="uk-icon uk-icon-send"/> }
            </a>
            </div>
          </div>
          { error && !hasChanged && <Alert message={error} type="error" key="err"/> }
        { warning && !hasChanged && <Alert message={warning} type="warning" key="warning"/> }
        { graderResponse }
        { mathjsError }
        </div>
  );
}
}

//Register the question component with the system
registerQuestionType('compareNumeric', QuestionCompareNumeric);
