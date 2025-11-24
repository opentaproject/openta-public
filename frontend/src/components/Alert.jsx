// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import PropTypes from 'prop-types';

export default class Alert extends Component {
  constructor() {
    super();
    this.alertRef = React.createRef();

  }

  static propTypes = {
    message: PropTypes.string,
    hasMath: PropTypes.bool,
    type: PropTypes.string,
    className: PropTypes.string
  };

  render() {
    var typeToClass = {
      success: 'uk-alert-success',
      warning: 'uk-alert-warning',
      error: 'uk-alert-danger',
      danger: 'uk-alert-danger'
    };
    var typeClass = this.props.type ? typeToClass[this.props.type] : '';
    return (
      <div ref={this.alertRef} 
        className={
          'uk-alert uk-overflow-container uk-margin-small-top uk-margin-small-bottom ' +
          typeClass +
          ' ' +
          this.props.className
        }
      >

         <div dangerouslySetInnerHTML={ {__html:  this.props.message  } } />
        {this.props.children}
      </div>
    );
  }

  componentDidUpdate(props, state, root) {
      var node = this.alertRef.current
      if (node !== null) {
        renderMathInElement(node, {
          delimiters: [{ left: '$', right: '$', display: false }]
        });
    }
  }
  componentDidMount(props, state, root) {
      var node = this.alertRef.current
      if (node !== null) {
        renderMathInElement(node, {
          delimiters: [{ left: '$', right: '$', display: false }]
        });
    }
  }
}
