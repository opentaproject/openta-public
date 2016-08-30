import React, { PropTypes, Component } from 'react';
import ReactDOM from 'react-dom';

export default class Alert extends Component {
  constructor() {
    super();
  }

  static propTypes = {
    message: PropTypes.string.isRequired,
    hasMath: PropTypes.bool,
    type: PropTypes.string
  }

  render() {
    var typeToClass = {
      success: 'uk-alert-success',
      warning: 'uk-alert-warning',
      error: 'uk-alert-danger'
    }
    var typeClass = this.props.type ? typeToClass[this.props.type] : "";
    return (
      <div className={"uk-alert " + typeClass} ref="alert">{this.props.message}</div>
    );
  }

  componentDidMount(props,state,root) {
    if(this.props.hasMath) {
      //var node = ReactDOM.findDOMNode(this.refs.alert);
      //MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
    }
  }
}
