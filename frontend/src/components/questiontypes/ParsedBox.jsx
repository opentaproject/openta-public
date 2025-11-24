import React, { Component } from 'react'; // React specific import
import PropTypes from 'prop-types';
import * as p from '../parse_latex.js';
import { external_renderAsciiMath } from './renderAsciiMath';

// Register function used at the bottom of this file to let the system know of the question type
import Alert from '../Alert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
// Another component useful for showing alerts in the form of colored boxes. See below for examples.
// Another component useful for showing badges in the form of small colored boxes. See below for examples.
//import latex from './latex.js';
import { throttle, debounce } from 'lodash';
import { create, all } from 'mathjs';
const math = create(all);

var unstableKey = 93;
const nextUnstableKey = () => unstableKey++;

const nexternal_renderAsciiMath = (text, thi) =>
  debounce((text, thi) => {
    return external_renderAsciiMath(text, thi);
  }, 500);

export default class ParsedBox extends Component {
  static propTypes = {
    thiss: PropTypes.object,
    isAuthor: PropTypes.bool, //Indicates if user is an author/content creator.
    input: PropTypes.string,
    submit: PropTypes.func,
    questionkey: PropTypes.string,
    pending: PropTypes.bool,
    allow_ai: PropTypes.bool,
  };

  constructor(props) {
    super(props);
    this.state = {
      input: this.props.input,
      rendered: '',
      cursor: 0,
      qvalue: '',
      ms: 100,
      qdef: this.props.input,
      not_first_time: false
    };
    this.unClosed = true;
    this.lastParsable = '';
    this.mathjserror = false;
    this.mathjswarning = '';
    this.varProps = {};
    this.timeoutID = '';
    this.rendered = '';
    this.timeoutID = null;
    this.varsList = undefined;
    this.validSymbols = ['pi', 'I', 'e', 'xhat', 'yhat', 'zhat', 't', 'x', 'y', 'z'];
    this.blacklist = [];
    this.parse_dispatch = {
      "'": p.prime
    };
    for (var item in p) {
      this.parse_dispatch[item.toString()] = p[item.toString()];
    }
  }
  handleChangeAscii = (event) => {
    if (event.target.value.match(/^[0-9a-zA-Z \}\{\:\?\n\*\\^\[\]\)\(,\.=\-\+\/\'\!\|\b]*$/)) {
      this.setState({ value: event.target.value });
      this.setState({ not_first_time: true });
    }
  };

 handleChangeUTF8 = (event) => {
      this.setState({ value: event.target.value });
      this.setState({ not_first_time: true });
  };


  newrenderAsciiMath = throttle(
    (asciitext, thiss) => {
      return external_renderAsciiMath(asciitext, thiss);
    },
    500,
    { leading: false, trailing: true }
  );
  nnewrenderAsciiMath = (asciitext, thiss) => external_renderAsciiMath(asciitext, thiss);

  // https://developer.mozilla.org/en-US/docs/Web/API/setTimeout
  //
  componentWillUnmount() {
    clearTimeout(this.timeoutID);
  }

  render() {
    if (this.state.value != null) {
      var changed = !(this.state.input.toString() == this.state.value.toString());
    } else {
      var changed = false;
    }
    var pvalue = this.state.value == undefined ? this.state.input : this.state.value;
    var firstChar = pvalue.trimStart()[0]; 
    var allow_ai = this.props.allow_ai
    var nomath = ( firstChar == '?')
    var domath = ! nomath ;
    var questionkey = this.props.questionkey;
    if( domath ){
    clearTimeout(this.timeoutID);
    if (this.state.rendered == '') {
      var start = Date.now();
      this.state.rendered = nomath? pvalue : this.nnewrenderAsciiMath(pvalue, this.props.thiss);
      this.state.ms = Date.now() - start;
    }

    var msdelay = 5 * this.state.ms;
    var smsdelay = String(msdelay);

    if (!(this.state.qvalue == pvalue)) {
      this.timeoutID = setTimeout(() => {
        this.setState({ qvalue: pvalue });
        var start = Date.now();
        this.setState({ rendered: this.nnewrenderAsciiMath(pvalue, this.props.thiss) });
        this.setState({ ms: Date.now() - start });
      }, msdelay);
    }
    var renderedResult = this.state.rendered;
    var renderedMath = renderedResult ? renderedResult.out : '';
    var syntaxerror = renderedResult.syntaxerror;
    var questionkey = this.props.questionkey;
    var sendcolor = syntaxerror || !this.state.not_first_time ? '' : ''; // "uk-button-success"
    var sendicon =
      syntaxerror || !this.state.not_first_time
        ? 'uk-icon uk-icon-ban uk-text-warning sendicon '
        : 'uk-icon uk-icon-send sendicon uk-text-success';
    }
   if ( domath ){
    sendicon = this.state.not_first_time ? sendicon : 'uk-icon uk-icon-pencil-square-o';
   } else {
    sendicon =  'uk-icon uk-icon-send sendicon uk-text-success';
   }
    /*
    if ( this.props.pending  ){
	    var color_style =  '#D3D3D3'
    } else {
	   var color_style = 'white'
    }
    */
    
    pvalue = allow_ai ? pvalue : pvalue.replace(/^\s*\?/, "");
    return (
      <div className={'uk-text ' + this.props.thiss.mathSizeClass}>
	{ this.props.pending && (
        <textarea
 	  disabled
          qkey={questionkey}
	  id={questionkey}
          className="uk-width-1-1 uk-textarea"
          key={'1234abc'}
          value={pvalue}
          onChange={this.handleChangeAscii}
        /> ) }
	{  domath &&  ! this.props.pending && (
         <textarea
          qkey={questionkey}
	  id={questionkey}
          className="uk-width-1-1 uk-textarea"
          key={'1234abc'}
          value={pvalue}
          onChange={this.handleChangeAscii}
        /> ) }
	{ nomath &&  ! this.props.pending && (
         <textarea
          qkey={questionkey}
	  id={questionkey}
          className="uk-width-1-1 uk-textarea"
          key={'1234abc'}
          value={pvalue}
          onChange={this.handleChangeUTF8}
        /> ) }

        {this.state.not_first_time && changed && (
          <div className="uk-text-left uk-width-1-1">
            <a onClick={(event) => this.props.submit(pvalue)} className={'uk-button click-send ' + sendcolor}>
              <i qkey={questionkey} className={sendicon} />
            </a>{' '}
          </div>
        )}
        {/* <button className="uk-button-small" key={'abcbut'}>{smsdelay}</button>  */}
        {this.state.not_first_time && changed && domath && (
          <Alert key={nextUnstableKey()} type="text" message={'$ ' + renderedMath + ' $'} hasMath={true} />
        )}
      </div>
    );
  }
}

export { ParsedBox };
