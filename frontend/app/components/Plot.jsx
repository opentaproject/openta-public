import React, { PropTypes, Component } from 'react';
import plotly from './plot.js';

export default class Plot extends Component {
  constructor() {
    super();
  }

  static propTypes = {
    data: PropTypes.array,
    layout: PropTypes.object,
    config: PropTypes.object,
  }

  componentWillUnmount() {
    plotly.purge(this.container);
  }
  componentDidMount() {
    let {data, layout, config} = this.props;
    plotly.newPlot(this.container, data, layout, config);
    //this.attachListeners();
  }

  componentDidUpdate(prevProps) {
    if (prevProps.data !== this.props.data || prevProps.layout !== this.props.layout) {
      plotly.newPlot(this.container, this.props.data, this.props.layout);
      //this.attachListeners();
    }
  }

  render() {
    return (
      <div ref={(node) => this.container = node}/>
    )
  }
}
