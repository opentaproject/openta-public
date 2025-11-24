import React, { Component } from 'react';
import PropTypes from 'prop-types';
import ReactDOM from 'react-dom';

export default class KatexSpan extends Component {
  constructor() {
    super();
  }

  static propTypes = {
    message: PropTypes.string,
    display: PropTypes.bool
  };

  static defaultProps = {
    display: false
  };

  createMarkup = (value) => {
    return { __html: value };
  };

  componentDidUpdate(props, state, root) {
    var node = ReactDOM.findDOMNode(this);
    if (node !== null) {
      renderMathInElement(node, {
        delimiters: [
          { left: '$', right: '$', display: this.props.display },
          { left: '\\[', right: '\\]', display: true }
        ]
      });
    }
  }
  componentDidMount(props, state, root) {
    var node = ReactDOM.findDOMNode(this);
    if (node !== null) {
      renderMathInElement(node, {
        delimiters: [
          { left: '$', right: '$', display: this.props.display },
          { left: '\\[', right: '\\]', display: true }
        ]
      });
    }
  }

  render() {
    return (
      <div
        className="uk-text-small uk-width-1-1 uk-margin-small-top uk-margin-small-right"
        dangerouslySetInnerHTML={this.createMarkup(this.props.message)}
      />
    );
  }
}
