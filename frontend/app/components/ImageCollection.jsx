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
    if(this.props.srcs.length > 0)
      return (
        <div className="uk-width-1-1">
        <div className="uk-button-group uk-margin-small-bottom">
          <button className="uk-button uk-button-small" type="button" onClick={this.onPrev}><i className="uk-icon uk-icon-chevron-left"/></button>
          <button className="uk-button uk-button-small" type="button" disabled>{this.state.activeImage+1}/{this.props.srcs.length}</button>
          <button className="uk-button uk-button-small" type="button" onClick={this.onNext}><i className="uk-icon uk-icon-chevron-right"/></button>
        </div>
        { this.props.badges && this.state.activeImage < this.props.badges.length &&
          <Badge className="uk-margin-small-left">{this.props.badges[this.state.activeImage]}</Badge>
        }
        <Image src={this.props.srcs[this.state.activeImage]}/>
        </div>
      )
    return (<span/>)
  }
}
