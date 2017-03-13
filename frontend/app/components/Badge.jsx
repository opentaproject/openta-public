import React, { PropTypes, Component } from 'react';
import ReactDOM from 'react-dom';

export default class Badge extends Component {
  constructor() {
    super();
  }

  static propTypes = {
    message: PropTypes.string,
    hasMath: PropTypes.bool,
    type: PropTypes.string,
    className: PropTypes.string,
    title: PropTypes.string,
  }

  render() {
    var typeToClass = {
      success: 'uk-badge-success',
      warning: 'uk-badge-warning',
      error: 'uk-badge-danger'
    }
    var typeClass = this.props.type ? typeToClass[this.props.type] : "";
    return (
      <div className={"uk-badge " + typeClass + " " + this.props.className} title={this.props.title}>{this.props.message}{this.props.children}</div>
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
