import React, { PropTypes , Component} from 'react';
import { connect } from 'react-redux';
import Codemirror from 'react-codemirror';
import immutable from 'immutable';

require('codemirror/addon/fold/foldcode');
require('codemirror/addon/fold/foldgutter');
require('codemirror/addon/fold/xml-fold');
require('codemirror/addon/hint/show-hint.js');
require('codemirror/addon/hint/xml-hint.js');
require('codemirror/mode/xml/xml');
require('codemirror/keymap/vim.js');

var CodeMirror = require('codemirror');
import {
  updateQuestionResponse,
  updateExerciseXML,
  updateExerciseActiveXML,
  updateExerciseJSON,
  updatePendingStateIn,
  setExerciseModifiedState,
  setExerciseXMLError,
} from '../actions.js';

// Make this presentational, pass state via props
var dummy = {
        attrs: {
        },
        children: []
      };
var tags = {
  "!top": ['exercise'],
  exercise: {
    children: ["exercisename", "text", "question", "figure", "solution"]
  },
  text: {
    children: ["figure"],
  },
  solution: {
    children: ["asset"]
  },
  asset: {
    attrs: {
      name: null
    }
  },
  global: {
    attrs: {
      type: ["compareNumeric", "multipleChoice"]
    }
  },
  question: {
    attrs: {
      key: null,
      type: ["compareNumeric", "multipleChoice"]
    },
    children: ["text", "expression", "choice", "variables"]
  },
  figure: {
    attrs: {
      size: ["small", "medium", "large"]
    }
  }
}

function completeAfter(cm, pred) {
  var cur = cm.getCursor();
  if (!pred || pred()) setTimeout(function() {
    if (!cm.state.completionActive)
      cm.showHint({completeSingle: false});
  }, 100);
  return CodeMirror.Pass;
}

function completeIfInTag(cm) {
  return completeAfter(cm, function() {
    var tok = cm.getTokenAt(cm.getCursor());
    if (tok.type == "string" &&
        (!/['"]/.test(tok.string.charAt(tok.string.length - 1)) ||
         tok.string.length == 1)) {
      return false;
    }
    var inner = CodeMirror.innerMode(cm.getMode(), tok.state).state;
    return inner.tagName;
  });
}

function settheme1(cm){
  cm.setOption("theme",'paraiso-light');
  cm.setOption("keyMap",'default');
}

function settheme2(cm){
  cm.setOption("theme",'rubyblue');
  cm.setOption("keyMap",'vim');
}

class XMLEditor extends Component {
  constructor(props) {
    super(props);
  }

  static propTypes = {
    xmlCode: PropTypes.string,
    onChange: PropTypes.func,
    theme: PropTypes.string,
  };

  render(){
    var xmlCode = this.props.xmlCode;
    var onChange = this.props.onChange;
    var options = {
      mode: 'xml',
      lineWrapping: true,
      lineNumbers: true,
      foldGutter: true,
      gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
      hintOptions: {schemaInfo: tags},
      extraKeys: {
        "'<'": completeAfter,
        "' '": completeIfInTag,
        "'='": completeIfInTag,
        "Ctrl-Space": "autocomplete",
        "Ctrl-5": settheme1,
        "Ctrl-6": settheme2,
        "Ctrl-7": onChange,
      },
    };
    return(
      <div className="uk-panel uk-panel-box uk-margin-small-top uk-margin-small-right" style={{height:"80vh"}}>
        <Codemirror value={xmlCode} options={options} onChange={onChange}/>
      </div>
    )
  }

}

export default XMLEditor;
