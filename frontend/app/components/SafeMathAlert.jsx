import React, { PropTypes, Component } from 'react';
import ReactDOM from 'react-dom';

export default class SafeMathAlert extends Component {
  constructor() {
    super();
  }

  static propTypes = {
    message: PropTypes.string.isRequired,
    type: PropTypes.string,
    className: PropTypes.string,
  }

  render() {
    var typeToClass = {
      success: 'uk-alert-success',
      warning: 'uk-alert-warning',
      error: 'uk-alert-danger'
    }
    var typeClass = this.props.type ? typeToClass[this.props.type] : "";
    try {
      var rendered = {
        __html: katex.renderToString(this.props.message)
      };
      return (
         <div className={"uk-alert uk-overflow-container " + typeClass + " " + this.props.className} ref="alert" dangerouslySetInnerHTML={rendered}></div>
      );
    }
    catch(e) {
      return (<div className={"uk-alert " + typeClass + " " + this.props.className} ref="alert"/>);
    }
  }
}
