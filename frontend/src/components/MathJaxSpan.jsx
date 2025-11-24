import React, { Component } from 'react';
import PropTypes from 'prop-types';

export default class MathSpan extends Component {
  constructor() {
    super();
    this.mathspanRef = React.createRef();
  }

  static propTypes = {
    html: PropTypes.string,       // mixed HTML + math delimiters
    message: PropTypes.string,    // optional (kept for backward compat)
    className: PropTypes.string
  };

  typesetMath = () => {
    const node = this.mathspanRef.current;
    if (node && window.MathJax) {
      window.MathJax.typesetClear?.([node]);
      window.MathJax.typesetPromise?.([node]).catch(err =>
        console.error('MathJax typeset failed:', err)
      );
    }
  };

  componentDidMount() {
    this.typesetMath();
  }

  componentDidUpdate(prevProps) {
    if (prevProps.html !== this.props.html || prevProps.message !== this.props.message) {
      this.typesetMath();
    } else {
      // Even if the string is "the same", React may have re-rendered children.
      this.typesetMath();
    }
  }

  render() {
    const { html, message, className, children } = this.props;
    //console.log("RENDERING WITH MATHAXSPAN")
    //console.log("HTML = ", html )


    // Prefer `html` when provided; fall back to message/children.
    // If using `html`, React won't escape it; you must trust/sanitize it.
    if (html != null) {
      return (
        <span
          ref={this.mathspanRef}
          className={className}
          dangerouslySetInnerHTML={{ __html: html }}
        />
      );
    }

    // Safe path: message/children rendered normally; include $...$ or $$...$$ inside.
    return (
      <span ref={this.mathspanRef} className={className}>
        {html}
        {children}
      </span>
    );
  }
}
