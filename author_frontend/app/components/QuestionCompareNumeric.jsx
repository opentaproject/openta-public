"use strict";
import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import immutable from 'immutable';

var inputClass = {
  error: 'uk-form-danger',
  correct: 'uk-form-success',
  incorrect: '',
  none: ''
};

class BaseQuestion extends Component {
  static propTypes = {
    questionData: PropTypes.object,
    submitFunction: PropTypes.func,
  }
  render() {  
  var data = this.props.questionData;
  var submit = this.props.submitFunction;
  return (
    <div>
      <div className="uk-panel uk-panel-box uk-margin-top" key={data.get('@key')}>
        <div className="uk-container">
          <label className="uk-form-row">{data.get('text','')}</label>
          <div className="uk-form-icon uk-width-1-1">
            <i className="uk-icon-pencil"/>
            <input className={"uk-width-1-1 "} type="text" onKeyUp={(event) => { if(event.keyCode === 13)submit(event.target.value) } }></input>
          </div>
        </div>
      </div>
    </div>
  );
}
}

const mapStateToProps = state => {
  return (
  {
    prop1: 'test'
  })
};

export default connect(mapStateToProps)(BaseQuestion)
