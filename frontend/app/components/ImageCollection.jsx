import React, { PropTypes, Component } from 'react';
import Image from './Image.jsx';
import Badge from './Badge.jsx';

export default class ImageCollection extends Component {
  constructor() {
    super();
    this.state = {
      activeImage: 0
    };
  }

  static propTypes = {
    srcs: PropTypes.array,
  }

  onNext = () => {
    if(this.state.activeImage + 1 < this.props.srcs.length)
      this.setState({
        activeImage: this.state.activeImage + 1
      });
  }
  onPrev = () => {
    if(this.state.activeImage - 1 >= 0)
      this.setState({
        activeImage: this.state.activeImage - 1
      });
  }
  render() {
    var renderImage = null;
    if(this.props.types[this.state.activeImage] === 'PDF') {
      renderImage = (
        <div className="uk-panel uk-panel-box">
        <h5 className="uk-panel-title">
          <a href={this.props.srcs[this.state.activeImage]} target="_blank">
            <i className="uk-icon uk-icon-medium uk-icon-justify uk-icon-file-pdf-o"/>Pdf file
          </a>
        </h5>
          <div className="uk-width-1-1" style={{height: '80vh'}}>
            <embed src={this.props.srcs[this.state.activeImage]} width="100%" height="100%"/>
          </div>
        </div>
      );
    }
    else {
      renderImage = (<Image src={this.props.srcs[this.state.activeImage]}/>);
    }
    if(this.props.srcs.length > 0)
      return (
        <div className="uk-width-1-1">
        <div className="uk-button-group uk-margin-small-bottom">
          <button className="uk-button uk-button-small" type="button" onClick={this.onPrev}><i className="uk-icon uk-icon-chevron-left"/></button>
          <button className="uk-button uk-button-small" type="button" disabled>{this.state.activeImage+1}/{this.props.srcs.length}</button>
          <button className="uk-button uk-button-small" type="button" onClick={this.onNext}><i className="uk-icon uk-icon-chevron-right"/></button>
        </div>
        { this.props.types[this.state.activeImage] === 'PDF' && <Badge className="uk-margin-small-left">pdf</Badge> }
        { this.props.types[this.state.activeImage] === 'IMG' && <Badge className="uk-margin-small-left">image</Badge> }
        { this.props.badges && this.state.activeImage < this.props.badges.length &&
          <Badge className="uk-margin-small-left">{this.props.badges[this.state.activeImage]}</Badge>
        }
        { renderImage }
        </div>
      )
    return (<span/>)
  }
}
