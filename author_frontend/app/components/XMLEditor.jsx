import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import Codemirror from 'react-codemirror';
require('codemirror/mode/xml/xml');

const BaseXMLEditor = ({ xmlCode, onChange }) => (
  <div className="uk-panel uk-panel-box">
    <Codemirror value={xmlCode} options={{mode: 'xml', lineWrapping: true, theme: 'monokai', lineNumbers: true}} onChange={onChange}/>
  </div>
);

const mapStateToProps = state => {
  var activeExerciseState = _.get(state.exerciseState, state.activeExercise, {});
  return {
    xmlCode: _.get(activeExerciseState, 'xml', '')
  }
};

const mapDispatchToProps = dispatch => {
  return {
    onChange: (xml) => console.log(xml)
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseXMLEditor)
