import React, { Component} from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Controlled as Codemirror } from 'react-codemirror2';
import immutable from 'immutable';
import vkbeautify from 'vkbeautify'
import AutoTranslate from './AutoTranslate.jsx';
import {handleSave,handleReset} from "./LoginInfo.jsx"
import { handleXMLChange } from './AuthorExercise.jsx';
import ExerciseHistory from './ExerciseHistory.jsx';
import DeleteExercise from './DeleteExercise.jsx';



require('codemirror/addon/display/autorefresh');
require('codemirror/addon/fold/foldcode');
require('codemirror/addon/fold/foldgutter');
require('codemirror/addon/fold/xml-fold');
require('codemirror/addon/hint/show-hint.js');
require('codemirror/addon/hint/xml-hint.js');
require('codemirror/mode/xml/xml');
require('codemirror/keymap/vim.js');

var CodeMirror = require('codemirror');
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

var Tools = ({showsave, onsave, savepending, savesuccess, saveerror, showreset, resetpending, onreset,use_auto_translation}) => (
    <div className="uk-button-group">
        {use_auto_translation && <AutoTranslate action={'remove'} /> }
        {use_auto_translation && <AutoTranslate action={'changedefaultlanguage'} />  }
        {use_auto_translation && <AutoTranslate action={'translate'} />  }
        { showsave && <a className={"uk-button uk-button-small " + (saveerror ? "uk-button-danger" : "uk-button-success")} onClick={onsave}>Save {savepending ? (<i className="uk-icon-cog uk-icon-spin"></i>) : (<i className="uk-icon-floppy-o"></i>)} </a> }
        { showreset && savepending !== true && <a className="uk-button uk-button-small uk-button-primary" title="Reset to last saved version." data-uk-tooltip onClick={onreset}> {resetpending ? (<i className="uk-icon-cog uk-icon-spin"></i>) : (<i className="uk-icon-undo"></i>)}</a> }
      <ExerciseHistory/>
      <DeleteExercise/>
        {!use_auto_translation && 
             <span className="uk-button uk-button-small uk-text uk-text-warning " title={'translations must be enabled in admin'} data-uk-tooltip >
                TRANSLATE OFF
                </span> }
    </div>
);

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
    this.state = {
      editor: this,
      readOnly: false,
      theme : 'paraiso-light',
      mode : 'default',
      keyMap: 'default',
    }
  }

  static propTypes = {
    xmlCode: PropTypes.string,
    onChange: PropTypes.func,
    theme: PropTypes.string,
    keyMap: PropTypes.string,
    activeXML: PropTypes.string,
    editor: PropTypes.object,
    suppresstools: PropTypes.bool,
  };

  keyMap_toggle = () => {
    var currentkeyMap = this.state.keyMap
    if (currentkeyMap == 'default') {
      this.setState({ keyMap: 'vim' })
    }
    else if (currentkeyMap == 'vim') {
      this.setState({ keyMap: 'default' })
    }
    else {
      this.setState({
        keyMap: 'default'
      })
    }
  }

  theme_toggle = () => {
    var current_theme = this.state.theme
    if (current_theme == 'paraiso-light') {
      this.setState({
        theme: 'rubyblue'
      })
    }
    else if (current_theme == 'rubyblue') {
      this.setState({
        theme: 'paraiso-light'
      })
    }
    else {
      this.setState({
        theme: 'paraiso-light'
      })
    }
  }

  prettify = () => {
    var editor = $('.CodeMirror')[0].CodeMirror
    var xml = vkbeautify.xmlmin(editor.getValue(), true) // true = preserve comments
    xml = xml.replace(/[\s\r\n]+/gm, ' ')
    xml = vkbeautify.xml(xml)
    xml = xml.replace(/^\s*[\r\n]/gm, '')
    editor.setValue(xml)
  }

  render(){
    var can_save = true
    var xmlCode = this.props.xmlCode;
    var onChange = this.props.onChange;
    var onReset = this.props.onReset;
    var exerciseState = this.props.exerciseState;
    var activeExercise = this.props.activeExercise;
    var savePending = exerciseState.get('savepending');
    var saveError = exerciseState.get('saveerror');
    var resetPending = exerciseState.get('resetpending');
    var modified = exerciseState.get('modified');
    var no_xml_error = exerciseState.get('xmlError') == null;
    var can_save = modified && no_xml_error;
    var suppresstools = false
    if ( this.props.suppresstools ){
        suppresstools = true 
        }

    var doshowtools = true
    if ( suppresstools  ){
        var doshowtools = false
        }
    var use_auto_translation = this.props.use_auto_translation
    // console.log("USE AUTO TRANSLATIONO = ", use_auto_translation)

    var savereset = (
      <Tools showsave={can_save} savepending={savePending} savesuccess={!modified && saveError === false} showreset={modified} saveerror={saveError} resetpending={resetPending} onsave={(event) => this.props.onSave(activeExercise)} onreset={(event) => onReset(activeExercise) } use_auto_translation={use_auto_translation} />
    );

    var options = {
      mode: 'xml',
      theme: this.state.theme,
      keyMap: this.state.keyMap,
      readOnly: false,
      lineWrapping: true,
      lineNumbers: true,
      foldGutter: true,
      gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
      hintOptions: {schemaInfo: tags},
      minFoldSize: 0,
      autoRefresh: true,
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
    return (
      <div className="uk-panel uk-panel-box uk-margin-small-top  uk-margin-small-right" style={{ height: "80vh", width: "100%" }}>
        { doshowtools && ( <a className={"uk-button uk-button-small  "} onClick={this.theme_toggle}>Switch theme {options.theme}</a> ) }
        { doshowtools && ( <a className={"uk-button uk-button-small "} onClick={this.keyMap_toggle}>Switch keymap {options.keyMap}</a> )}
        { doshowtools && ( <a className={"uk-button uk-button-small  "} onClick={this.prettify}> Prettify </a> )}
        { doshowtools && ( 
      <Tools showsave={can_save} use_auto_translation={this.props.use_auto_translation} savepending={savePending} savesuccess={!modified && saveError === false} showreset={modified} saveerror={saveError} resetpending={resetPending} onsave={(event) => this.props.onSave(activeExercise)} onreset={(event) => onReset(activeExercise)} />
             ) }
        <Codemirror value={xmlCode} options={options} onBeforeChange={this.props.onChange} editorDidMount={this.editorDidMount} editorDidConfigure={this.editorDidConfigure}
          editorWillUnmount={this.editorWillUnmount} />
      </div>
    )
  }


}

const mapStateToProps = state => {
  var activeExerciseState = state.getIn(['exerciseState', state.get('activeExercise')], immutable.Map({}));
  var activeCourse = state.getIn(['activeCourse'])
  return ({
    exerciseKey: state.get('activeExercise'),
    activeCourse: activeCourse,
    course: state.getIn(['courses', activeCourse, 'course_name'], ""),
    activeExercise: state.get('activeExercise'),
    exerciseState: activeExerciseState,
    activeXML: activeExerciseState.getIn(['activeXML']),
    editor: state.editor,
    languages:  state.getIn(['course', 'languages'],['none']),
    lang: state.get('lang'),
    editor: state.editor,
    use_auto_translation: state.getIn(['courses',activeCourse,'use_auto_translation'])
});
}

const mapDispatchToProps = dispatch => ({
    onXMLEditorClick: (event) => dispatch(updateActiveAdminTool('xml-editor')),
    onOptionsClick: (event) => dispatch(updateActiveAdminTool('options')),
    onStatisticsClick: (event) => dispatch(updateActiveAdminTool('statistics')),
    onSave: (exercise) => dispatch(handleSave(exercise)),
    onReset: (exercise) => dispatch(handleReset(exercise)),
    onHome: () => dispatch(navigateMenuArray([])),
    onXMLChange: (xml, exercise, flagModified=true) => dispatch(handleXMLChange(xml, exercise, flagModified)) ,

});

export default connect(mapStateToProps, mapDispatchToProps)(XMLEditor)
