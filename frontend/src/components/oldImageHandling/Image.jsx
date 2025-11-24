// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { Component } from 'react';
import PropTypes from 'prop-types';
import {fabric} from 'fabric';

export default class Image extends Component {
  constructor() {
    super();
    this.state = {
      angle: 0,
      scale: 1
    };
  }

  static propTypes = {
    src: PropTypes.string,
  }

  resize = () => {
    if(this.container && this.canvas) {
      this.canvas.setWidth(this.container.clientWidth);
      this.canvas.calcOffset();
    }
  }

  UNSAFE_componentWillUnmount() {
    window.removeEventListener('resize', this.resize);
  }

  componentDidMount() {
    window.addEventListener('resize', this.resize);
    var space = window.innerHeight - this.canvasref.offsetTop
    this.canvasref.width  = this.container.clientWidth;
    if(this.props.viewportHeight)
      this.canvasref.height = space * 0.7;
    else
      this.canvasref.height = this.container.clientWidth;
    this.canvas = new fabric.Canvas('imagecanvas');
    this.canvas.backgroundColor = 'rgba(0,0,0, 0.2)';
    fabric.Image.fromURL(this.props.src, oImg => {
      oImg.scaleToWidth(this.canvas.getWidth());
      var tmpScale = oImg.getScaleX;
      oImg.scaleToHeight(this.canvas.getHeight());
      if(tmpScale < oImg.getScaleX)
        oImg.scaleToWidth(this.canvas.getWidth());
      this.canvas.add(oImg);
      this.canvas.centerObject(oImg);
    });
  }

  componentDidUpdate(prevProps) {
    if(this.props.src && this.props.src !== prevProps.src) {
      this.canvas.clear();
      fabric.Image.fromURL(this.props.src, oImg => {
        oImg.scaleToWidth(this.canvas.getWidth());
        var tmpScale = oImg.getScaleX;
        oImg.scaleToHeight(this.canvas.getHeight());
        if(tmpScale < oImg.getScaleX)
          oImg.scaleToWidth(this.canvas.getWidth());
        this.state.scale = 1;
        this.state.angle = 0;
        this.canvas.add(oImg);
        this.canvas.centerObject(oImg);
      });
    } else {
      if(this.canvas.item(0)) {
        var image = this.canvas.item(0);
        var center = new fabric.Point(this.canvas.getWidth() / 2, this.canvas.getHeight() /2);
        image.rotate(this.state.angle);
        this.canvas.zoomToPoint(center, this.state.scale);
        this.canvas.requestRenderAll();
      }
    }
  }

  onRotateLeft = () => {
    this.setState({
      angle: this.state.angle - 90
    });
  }
  onRotateRight = () => {
    this.setState({
      angle: this.state.angle + 90
    });
  }
  onZoomIn = () => {
    this.setState({
      scale: this.state.scale*1.2
    });
  }
  onZoomOut = () => {
    this.setState({
      scale: this.state.scale*0.8
    });
  }

  render() {
    return (
      <div className="uk-width-1-1" ref={ (node) => this.container = node }>
      { this.props.src &&
      <div className="uk-button-group">
        <button className="uk-button uk-button-small" onClick={this.onRotateLeft}><i className="uk-icon uk-icon-rotate-left"/></button>
        <button className="uk-button uk-button-small" onClick={this.onRotateRight}><i className="uk-icon uk-icon-rotate-right"/></button>
        <button className="uk-button uk-button-small" onClick={this.onZoomOut}><i className="uk-icon uk-icon-search-minus"/></button>
        <button className="uk-button uk-button-small" onClick={this.onZoomIn}><i className="uk-icon uk-icon-search-plus"/></button>
        <a className="uk-button uk-button-small" href={this.props.src}><i className="uk-icon uk-icon-file-photo-o"/></a>
      </div>
      }
      <canvas id="imagecanvas" ref={ (node) => this.canvasref = node }></canvas> 
      </div>
    )
  }
}
