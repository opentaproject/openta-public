/*
 * This is the presentational part of a question. It contains the javascript and html code that is shown in the front-end to the user.
 * It consists of a React component (see documentation on github for more details).
 */
'use strict'; // It is recommended to use strict javascript for easier debugging

import immutable from 'immutable';
import { store } from '../../store';
import { connect } from 'react-redux';
import React, { Component } from 'react'; // React specific import
//import ReactDOMServer from 'react-dom/server';
import { lazy } from 'react';
import PropTypes from 'prop-types';

import { fetchExerciseJSON } from '../../fetchers.js';
import { registerQuestionType } from './question_type_dispatch.jsx'; // Register function used at the bottom of this file to let the system know of the question type
const CKEditor = lazy(() => import('@ckeditor/ckeditor5-react'));
const ClassicEditor = lazy(() => import('@ckeditor/ckeditor5-build-classic'));
//import { CKEditor } from '@ckeditor/ckeditor5-react';
//import { ClassicEditor } from '@ckeditor/ckeditor5-build-classic';
const XMLEditor = lazy(() => import('../XMLEditor.jsx'));
import TextareaEditor from '../TextareaEditor.jsx';
var unstableKey = 93;
const nextUnstableKey = () => unstableKey++;

import Alert from '../Alert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
// Another component useful for showing badges in the form of small colored boxes. See below for examples.
import HelpWebworks from './HelpWebworks.jsx';
import T from '../Translation.jsx';
import t from '../../translations.js';
import { throttle } from 'lodash';



class QuestionWebworks extends Component {
  static propTypes = {
    // questionData: PropTypes.object, // Data from exercise XML file, i.e. whats inside the <question> tag
    iref: PropTypes.object,
    questionState: PropTypes.object, // Current question state together with response data from server
    submitFunction: PropTypes.func, // Call this function to submit an answer to the server. The only parameter is the answer data which is unconstrained: It could be a simple string as below or a dictionary of values if more information needs to be conveyed.
    questionPending: PropTypes.bool, // Indicates when we are waiting for a server response
    message: PropTypes.string,
    isAuthor: PropTypes.bool, //Indicates if user is an author/content creator.
    canViewSolution: PropTypes.bool, //Indicates if user is allowed to see solution.
    exerciseKey: PropTypes.string,
    exerciseState: PropTypes.object,
    pendingState: PropTypes.object,
    submits: PropTypes.string,
    assets: PropTypes.object,
  };

  constructor(props) {
    super(props);
    this.state = {
      message: null,
      iframekey: 'kk',
      submits: '0',
      value: this.props.questionState.getIn(['answer'], ''),
      mathSize: 'medium',
      cursor: 0,
      exerciseKey: this.props.exerciseKey,
      exerciseState: this.props.exerciseState,
      pending: this.props.pendingState.getIn(['exerciseList']) ,
      data: "",
      nrenders: 0 ,
      assets: this.props.assets,
    };


  }



  handleChange = (event) => {
    this.setState({ value: event.target.value });
  };

  handleCKChange = (event, editor) => {
    const data = editor.getData();
    this.setState({ value: data });
  };

  updateCursor = throttle((pos) => {
    this.setState({ cursor: pos });
  }, 500);

  handleSelect = (event) => {
    this.updateCursor(event.target.selectionStart);
  };

  setMathSize = (sizeStr) => {
    this.setState({ mathSize: sizeStr });
  };

  // UNSAFE_componentWillReceiveProps = newProps => {};

  valueUpdate = (value) => {
    this.setState({ value: value });
  };

  createMarkup = (value) => {
    return { __html: value };
  };

  /* render gets called every time the question is shown on screen */
  render() {
    // Some convenience definitions
    //console.log("PENDING = ", this.state.pending)
    var exerciseKey = this.props.exerciseKey;
    //console.log("exerciseKey = ", exerciseKey )
    var exerciseState = this.props.exerciseState;
    var solution = exerciseState.getIn(['solution'],null)
   // console.log("solution = ", exerciseState.toJS() )
//    console.log("exerciseState = ", exerciseState )
    var question = this.props.questionData;
    var assets_length = this.state.assets.toJS().length ;
//    console.log("ASSETS_LENGTH = ", assets_length );
//    console.log("QUESTION = ", question.toJS() )
    var source = question.getIn(['source','$'],null )
//    console.log("SOURCE = ", source )
    var state = this.props.questionState;
//    console.log("STATE = ", state.toJS()  )
    var submit = this.props.submitFunction;
    var answerbox = question.getIn(['@attr', 'answerbox'], true);
    var notanswerbox = false;
    if (answerbox == 'false' || answerbox == 'False') {
      answerbox = false;
      notanswerbox = true;
    } else {
      answerbox = true;
      notanswerbox = false;
    }
    this.state.nrenders = this.state.nrenders + 1 ;
//    console.log("NRENDERS + ", this.state.nrenders)

    // System state data
    var lastAnswer = state.getIn(['answer'], ''); // Last saved answer in database, same format as passed to the submitFunction
    var correct = state.getIn(['response', 'correct'], null); // || state.getIn(["correct"], null); // Boolean indicating if the grader reported correct answer
    //var correct = state.getIn(["response", "correct"], false) || state.getIn(["correct"], false); // Boolean indicating if the grader reported correct answer
    var n_attempts = state.getIn(['response', 'n_attempts'], question.getIn(['n_attempts'], 0));
    var previous_answers = state.getIn(['response', 'previous_answers'], question.getIn(['previous_answers'], []));
    var editor_type = state.getIn(['response', 'editor'], question.getIn(['editor'], 'default'));
    // override default true xml of feedback with options
    if (state.getIn(['correct'], null) == null) {
      var feedback = false;
    } else {
      var feedback = true;
    }

    var error = state.getIn(['response', 'error']); // Custom field containing error information
    var author_error = state.getIn(['response', 'author_error']); // Custom field containing error information
    var warning = state.getIn(['response', 'warning']); // Custom field containing error information
    var hint = state.getIn(['response', 'hint']); // Custom field containing error information
    var comment = state.getIn(['response', 'comment'], '');
    var tdict = state.getIn(['response', 'dict'], '');
    if (state.getIn(['response', 'detail'])) {
      error =
        'Ett fel uppstod. (Detta kan bero på att du inte är inloggad, om problem kvarstår var vänlig hör av dig.)';
    }

    var graderResponse = null;
    var input = this.state.value;
    if ('' == input) {
      var p = previous_answers;
      if (p.length > 0) {
        input = p[0].answer;
      }
    }
    if (notanswerbox) {
      input = ' '; // MAKE THIS A BLANK SO AS NOT TO TRIGGER A NOOP in fetchers.js/questionCheck
    }

    var hasChanged = input !== lastAnswer;
//    console.log("HAS CHANGED = ", hasChanged)
    var nonEmpty = input !== '';
    var unchecked = '(' + t('unchecked') + ')';
    var itemjson = question.getIn(['text'], undefined);
    var questiontext = this.props.renderText(itemjson);
    var questionkey = question.getIn(['@attr', 'key']);
    var show_solution = this.props.exerciseState.getIn(['meta','solution'], false ) ;
    console.log("SHOW SOLUTION = ", show_solution)
    var msg1 = 'QuestionType QuestionWebworks';
    var sourceFilePath = String( state.getIn(["assetpath"],"") ) + "/" + source;
    var seed =  String( state.getIn(["seed"],""))
    var permissionLevel = this.props.isAuthor ? "20" :  "0";
    var userkey = state.getIn(['user'])
    var identifier = state.getIn(["identifier"],'identifer-from-jsx');
    var studentAssetPath = String( state.getIn(["studentAssetPath"],'studentAssetPath-from-jsx') );
    var outputFormat = show_solution ?  String( state.getIn(["outputFormat"],'simple ') ) : String( state.getIn(["outputFormat"],'single') );
    var indexExists = state.getIn(["indexExists"] );
//    console.log("indexExists = ", indexExists )
//    console.log("STUDENT_ASSET_PATH = ", studentAssetPath )
    console.log("COMPUTED outputFormat = ", outputFormat )
    var id = 'ABC';
    // var src = "/exercise/112346b5-150c-4320-98c1-bf9d5a419db5/asset/iframe.html" // DEMO USING PASSBACK ; abandoned
    //var src = "http://localhost:3000/render-api?" + sourceFilePath + "&problemSeed=" + seed  + "&outputFormat=classic&permissionLevel=" + permissionLevel + "&identifier=" + identifier + "&studentAssetPath=" + studentAssetPath ;
    //console.log("OUTPUTFORMAT = ", outputFormat )
    var src = "./webwork_forward/?sourceFilePath=" + sourceFilePath + "&problemSeed=" + seed  + "&outputFormat=" + outputFormat + "&permissionLevel=" + permissionLevel + "&identifier=" + identifier + "&studentAssetPath=" + studentAssetPath ;
    var splits =  studentAssetPath.split('/')
//    console.log("SPLITS = ", splits, splits[6] )
    if (indexExists  && ! this.props.isAuthor ){ // Let author html be regenerated
    	var src = 'exercise/' + splits[7] + '/studentasset/index.html';
    };
//    console.log("src ", src )
    // This piece of code is designed to force a render when live editig the pg file but not if there is a submit
    // var src = "exercise/d12f61e3-f60c-49f9-8a1d-5dddda50b35f/asset/index.html";
    // src = 'exercise/d12f61e3-f60c-49f9-8a1d-5dddda50b35f/studentasset/index.html';
//    console.log("src = ", src )
//    console.log("stdudentAssetPath = ", studentAssetPath )
    if( this.state.message ) {
	    console.log("MESSAGE EXISTS");
	    var iframekey=this.state.iframekey
	    this.state.submits = String( parseInt( this.state.submits ) + 1 );
	     } else {
	    //console.log("NO MESSAGE EXISTS");
	    var iframekey=this.state.iframekey
	      // iframekey = iframekey + this.state.nrenders
	      this.state.iframekey = iframekey;
	     }
     //console.log("IFRAMEKEY= ", this.state.submits, "KEY = ", iframekey)
     if ( this.state.submits > 1 && this.props.isAuthor  ){
	     this.state.iframekey = '';
	     this.state.submits = '0';
     }
     var h = window.innerHeight - 100 ;
     console.log("HEIGHT = ", h )
     return (
      <div className="uk-width-1-1" key={iframekey} id={'qw-' + this.state.nrenders} >
        <div>
          <h4>{this.state.message}</h4>
        </div>
        <iframe
          className="iframe"
	  width="100%"
	  height={h}
          title="TMS WebCore IFrame"
          src={src}
        />
      </div>
    );
  }
// https://stackoverflow.com/questions/34743264/how-to-set-iframe-content-of-a-react-component
// https://codesandbox.io/s/react-iframe-postmessage-demo-stn39?file=/tsconfig.json
// https://javascriptbit.com/transfer-data-between-parent-window-and-iframe-postmessage-api/
// https://codesandbox.io/s/react-iframe-postmessage-demo-stn39
// https://stackoverflow.com/questions/34743264/how-to-set-iframe-content-of-a-react-component
	//
nocomponentDidUpdate(prevProps, prevState) {
  console.log("DID UPDATE", this.state.message);
  console.log("DID UPDATE assets = ", this.state.assets );
  console.log("DID UPDATE exerciseState = ", this.state.exerciseState.toJS());
  console.log("DID UPDATE pending = ", this.state.pending)
  if (prevState.message !== this.state.message) {
    console.log('message has changed.')
  }
  if (prevState.pending !== this.state.pending ) {
    console.log('pendingState has changed.')
  }
  if (prevState.exerciseState !== this.state.exerciseState ) {
    console.log('state has changed.')
  }
}
 componentDidMount() {
    window.addEventListener(
      "message",
      (ev ) => {
        if (typeof ev.data !== "object") return;
        if (!ev.data.type) return;
        if (ev.data.type !== "button-click") return;
        if (!ev.data.message) return;
	console.log("EVENT FIRED", ev.data )
        this.setState({
          message: ev.data.message + this.state.nrenders
        });
      }
    );
  }


 }


const mapStateToProps = (state) => {
  //var exerciseState = _.get(state.exerciseState, state.activeExercise, {});
  var exerciseState = state.getIn(['exerciseState', state.get('activeExercise')], immutable.Map({}));
  return {
    assets: exerciseState.getIn(['assets'], immutable.List([])),
    exerciseState: exerciseState,
  };
};





export default connect(mapStateToProps, null)(QuestionWebworks);
//Register the question component with the system
registerQuestionType('webworks', QuestionWebworks);

