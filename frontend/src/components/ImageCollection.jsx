// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { Component } from 'react';
import PropTypes from 'prop-types';
import Image from './Image.jsx';
import Badge from './Badge.jsx';
import PDFAnnotationTools from './PDFAnnotationTools';
import { env_source , adobe_id } from '../settings';


export default class ImageCollection extends Component {
  constructor() {
    super();
    this.state = {
      activeImage: 0
    };
  }

  static propTypes = {
    srcs: PropTypes.array,
    exerciseKey: PropTypes.string,
  };

  onNext = () => {
    if (this.state.activeImage + 1 < this.props.srcs.length) {
      this.setState({
        activeImage: this.state.activeImage + 1
      });
    }
  };
  onPrev = () => {
    if (this.state.activeImage - 1 >= 0) {
      this.setState({
        activeImage: this.state.activeImage - 1
      });
    }
  };
  render() {
    var renderImage = null;
    var exerciseKey = this.props.exerciseKey 
    if (this.props.types[this.state.activeImage] === 'PDF') {
      renderImage = (
        <div className="uk-panel uk-panel-box">
          <h5 className="uk-panel-title">
            <a href={this.props.srcs[this.state.activeImage]} target="_blank" rel="noreferrer">
              <i className="uk-icon uk-icon-medium uk-icon-justify uk-icon-file-pdf-o" />
              Pdf file
            </a>
          </h5>
	  { adobe_id == '' && ( 
          <div className="uk-width-1-1" style={{ height: '80vh' }}>
            <embed
              key={this.state.activeImage}
              src={this.props.srcs[this.state.activeImage]}
              width="100%"
              height="100%"
              type="application/pdf"
            />
	</div>  ) }
	  { adobe_id != '' && ( 
	  <div key={this.state.activeImage} className="uk-width-1-1" style={{ height: '80vh' }}>
		
            <PDFAnnotationTools imagekey={this.state.activeImage} exerciseKey={exerciseKey} src={this.props.srcs[this.state.activeImage]} />
          </div> )}
        </div>
      );
    } else {
      renderImage = <Image src={this.props.srcs[this.state.activeImage]} />;
    }
    if (this.props.srcs.length > 0) {
      return (
        <div className="uk-width-1-1">
          <div className="uk-button-group uk-margin-small-bottom">
            <button className="uk-button uk-button-small" type="button" onClick={this.onPrev}>
              <i className="uk-icon uk-icon-chevron-left" />
            </button>
            <button className="uk-button uk-button-small" type="button" disabled>
              {this.state.activeImage + 1}/{this.props.srcs.length}
            </button>
            <button className="uk-button uk-button-small" type="button" onClick={this.onNext}>
              <i className="uk-icon uk-icon-chevron-right" />
            </button>
          </div>
          {this.props.types[this.state.activeImage] === 'PDF' && <Badge className="uk-margin-small-left">pdf</Badge>}
          {this.props.types[this.state.activeImage] === 'IMG' && <Badge className="uk-margin-small-left">image</Badge>}
          {this.props.badges && this.state.activeImage < this.props.badges.length && (
            <Badge className="uk-margin-small-left">{this.props.badges[this.state.activeImage]}</Badge>
          )}
          {renderImage}
        </div>
      );
    }
    return <span />;
  }
}
