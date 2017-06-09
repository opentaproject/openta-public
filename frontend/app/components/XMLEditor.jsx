import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import Codemirror from 'react-codemirror';
require('codemirror/addon/fold/foldcode');
require('codemirror/addon/fold/foldgutter');
require('codemirror/addon/fold/xml-fold');
require('codemirror/addon/hint/show-hint.js');
require('codemirror/addon/hint/xml-hint.js');
require('codemirror/mode/xml/xml');
var CodeMirror = require('codemirror');

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
      type: ["ClonedCompareNumeric","compareNumeric", "multipleChoice"]
    }
  },
  question: {
    attrs: {
      key: null,
      type: ["ClonedCompareNumeric","compareNumeric", "multipleChoice"]
    },
    children: ["text", "expression", "choice", "variables"]
  },
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
          if (tok.type == "string" && (!/['"]/.test(tok.string.charAt(tok.string.length - 1)) || tok.string.length == 1)) return false;
          var inner = CodeMirror.innerMode(cm.getMode(), tok.state).state;
          return inner.tagName;
        });
      }

export default ({ xmlCode, onChange }) => (
  <div className="uk-panel uk-panel-box uk-margin-small-top uk-margin-small-right" style={{height:"80vh"}}>
    <Codemirror value={xmlCode} options={{
      mode: 'xml', 
      lineWrapping: true, 
      theme: 'paraiso-light', 
      lineNumbers: true,
      foldGutter: true,
      gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
      hintOptions: {schemaInfo: tags},
      extraKeys: {
           "'<'": completeAfter,
           "' '": completeIfInTag,
           "'='": completeIfInTag,
          "Ctrl-Space": "autocomplete"
        },
    }} onChange={onChange}/> 
  </div>
);

/*const mapStateToProps = state => {
  var activeExerciseState = _.get(state.exerciseState, state.activeExercise, {});
  return {
    xmlCode: _.get(activeExerciseState, 'xml', '')
  }
};

const mapDispatchToProps = dispatch => {
  return {
    onChange: (xml) => console.log(xml)
  }
}*/

//export default connect(mapStateToProps, mapDispatchToProps)(BaseXMLEditor)
