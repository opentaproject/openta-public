import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import Codemirror from 'react-codemirror';
require('codemirror/mode/xml/xml');

const BaseXMLEditor = ({ xmlCode }) => (
  <div className="uk-panel uk-panel-box">
    <Codemirror value={xmlCode} options={{mode: 'xml'}}/>
  </div>
);

const mapStateToProps = state => (
  {
    xmlCode: "<root></root>"
  }
);

export default connect(mapStateToProps)(BaseXMLEditor)
