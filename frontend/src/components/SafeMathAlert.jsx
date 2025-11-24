// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { Component, createRef } from 'react';
import PropTypes from 'prop-types';

export default class SafeMathAlert extends Component {
  constructor() {
    super();
    this.myalert = createRef();  // ← replace string ref
  }

  static propTypes = {
    message: PropTypes.string.isRequired,
    type: PropTypes.string,
    className: PropTypes.string
  };

  render() {
    var typeToClass = {
      success: 'uk-alert-success',
      warning: 'uk-alert-warning',
      error: 'uk-alert-danger'
    };
    var typeClass = this.props.type ? typeToClass[this.props.type] : '';
    try {
      var rendered = {
        __html: katex.renderToString(this.props.message)
      };
      return (
        <div
          className={'uk-alert uk-overflow-container ' + typeClass + ' ' + this.props.className}
          ref={this.myalert}  // ← updated
          dangerouslySetInnerHTML={rendered}
        ></div>
      );
    } catch (e) {
      return (
        <div
          className={'uk-alert ' + typeClass + ' ' + this.props.className}
          ref={this.myalert}  // ← updated
        />
      );
    }
  }
}
