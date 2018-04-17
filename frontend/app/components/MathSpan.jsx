import React, { Component } from 'react';
import PropTypes from 'prop-types';
import ReactDOM from 'react-dom';

export default class MathSpan extends Component {
  constructor() {
    super();
  }

  static propTypes = {
    message: PropTypes.string,
    display: PropTypes.bool,
  }

  static defaultProps = {
    display: false,
  }

  componentDidUpdate(props,state,root) {
    var node = ReactDOM.findDOMNode(this);
    if(node !== null)
      renderMathInElement(node, {
        delimiters: [{left: "$", right: "$", display: this.props.display}]
      });
  }
  componentDidMount(props,state,root) {
    var node = ReactDOM.findDOMNode(this);
    if(node !== null)
      renderMathInElement(node, {
        delimiters: [{left: "$", right: "$", display: this.props.display}]
      });
  }

  render() {
         return (<span className={this.props.className}>{this.props.message}{this.props.children}</span>)
  }
}
