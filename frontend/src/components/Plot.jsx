import React, { Component } from 'react';
import PropTypes from 'prop-types';
//import plotly from './plot.js';
// import plotly from 'plotly.js-cartesian-dist-min';


export default class Plot extends Component {
  constructor() {
    super();
  }

  static propTypes = {
    data: PropTypes.array,
    layout: PropTypes.object,
    config: PropTypes.object,
    plotkey: PropTypes.string,
  };


  componentDidMount() {
    let data = this.props.data;
    let config = this.props.config
    let plotkey = this.props.plotkey ? this.props.plotkey : 'thisplotkey'
    let layout=this.props.layout
    import('plotly.js-cartesian-dist-min').then((plotly) => {
	 var out = plotly.validate(data,layout);
	 if (out &&  this.props.showerrors ){
		data = [{}];
		layout = {title: out[0].msg}
	 };
	 plotly.newPlot(plotkey , data, layout, config)
    })
    //this.attachListeners();
  }

componentDidUpdate(prevProps) {
    let plotkey = this.props.plotkey ? this.props.plotkey : 'thisplotkey2'
    if (prevProps.data !== this.props.data || prevProps.layout !== this.props.layout) {
     import('plotly.js-cartesian-dist-min').then((plotly) => {
      plotly.newPlot(plotkey, this.props.data, this.props.layout, { staticPlot: false });
	var out = plotly.validate(this.props.data,this.props.layout);
	if (out &&  this.props.showerrors ){
		data = [{}];
		layout = {title: out[0].msg}
	 };
	plotly.newPlot(plotkey, this.props.data, this.props.layout, { staticPlot: false })
      })
   //this.attachListeners();
  }
 }
 
 render() {
    let plotkey = this.props.plotkey ? this.props.plotkey : 'thisplotkey'
    return ( <div  id={plotkey} /> )
  }
}

