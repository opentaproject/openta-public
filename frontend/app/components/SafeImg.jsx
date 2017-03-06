import React, { PropTypes, Component } from 'react';
import ReactDOM from 'react-dom';

export default class SafeImg extends Component {
  constructor() {
    super();
    this.state = { error: false }
  }

  static propTypes = {
    src: PropTypes.string,
  }

  onError = (event) => {
    this.setState({error: true});
  }

  render() {
    if(this.state.error)
      return (<div className={this.props.className}>{this.props.children}</div>);
    else
      return (<img src={this.props.src} style={this.props.style} className={this.props.className} width={this.props.width} height={this.props.height} onError={this.onError}/>)
  }
}
