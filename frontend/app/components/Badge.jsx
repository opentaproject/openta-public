import React, { PropTypes, Component } from 'react';
import ReactDOM from 'react-dom';

export default class Badge extends Component {
  constructor() {
    super();
  }

  static propTypes = {
    message: PropTypes.string.isRequired,
    hasMath: PropTypes.bool,
    type: PropTypes.string,
    className: PropTypes.string
  }

  render() {
    var typeToClass = {
      success: 'uk-alert-success',
      warning: 'uk-alert-warning',
      error: 'uk-alert-danger'
    }
    var typeClass = this.props.type ? typeToClass[this.props.type] : "";
    return (
      <div className={"uk-badge " + typeClass + " " + this.props.className}>{this.props.message}</div>
    );
  }

  componentDidUpdate(props,state,root) {
    if(this.props.hasMath) {
    var node = ReactDOM.findDOMNode(this);
    //MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
    if(node !== null)
      renderMathInElement(node, {
        delimiters: [{left: "$", right: "$", display: false}]
      });
      //var node = ReactDOM.findDOMNode(this.refs.alert);
      //MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
    }
  }
  componentDidMount(props,state,root) {
    if(this.props.hasMath) {
    var node = ReactDOM.findDOMNode(this);
    //MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
    if(node !== null)
      renderMathInElement(node, {
        delimiters: [{left: "$", right: "$", display: false}]
      });
      //var node = ReactDOM.findDOMNode(this.refs.alert);
      //MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
    }
  }
}
