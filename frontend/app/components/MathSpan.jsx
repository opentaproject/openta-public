import React, { PropTypes, Component } from 'react';
import ReactDOM from 'react-dom';

export default class MathSpan extends Component {
  constructor() {
    super();
  }

  static propTypes = {
    message: PropTypes.string.isRequired,
  }

  componentDidUpdate(props,state,root) {
    var node = ReactDOM.findDOMNode(this);
    if(node !== null)
      renderMathInElement(node, {
        delimiters: [{left: "$", right: "$", display: false}]
      });
  }
  componentDidMount(props,state,root) {
    var node = ReactDOM.findDOMNode(this);
    if(node !== null)
      renderMathInElement(node, {
        delimiters: [{left: "$", right: "$", display: false}]
      });
  }

  render() {
         return (<span>{this.props.message}</span>)
  }
}
