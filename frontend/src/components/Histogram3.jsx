// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { Component } from 'react';
import PropTypes from 'prop-types';
import Plot from './Plot.jsx';
import {add} from 'mathjs';

function generateScatterPlot(renderResultsObject) {
  //{{{
  var j = renderResultsObject.toJS();
  var x = j.map(( item ) => item.total_correct_queries)
  var y = j.map(( item ) =>  item.total_queries  ) // - item.total_correct_queries)
  var text =  j.map(( item ) => item.username )
  var plotData = {
  x: x, 
  y: y,
  text: text,
  mode: 'markers',
  type: 'scatter',
  name: 'total-vs-correct',
  marker: { size: 6 , color: 'blue' }
  };
  var xmax =  Math.max(...x);
  var layout = {xaxis: { title: "Total correct queries "},
  		yaxis: { title:  "Total queries "} 
  		};
  var line1 = { x: [0,xmax],
	        y: [0,xmax],
  	        mode: 'lines',
	  	line: { color: 'green',width: 2 },
                name: 'x=y' } 

  var line2 = { x: [0,xmax],
	        y: [0,2 * xmax],
	      mode: 'lines',
   	      name: 'y=2x '};
  var line3 = { x: [0,xmax],
	        y: [0,3 * xmax],
	      mode: 'lines',
   	      name: 'y=3x '};
  return {
    data: [ line1, line2,line3, plotData],
    layout: layout
  };
} //}}}

export default class Histogram3 extends Component {
  constructor() {
    super();
    this.state = { error: false };
  }

  static propTypes = {
    renderResults: PropTypes.object
  };

  render() {
    var { data: histData, layout: layout } = generateScatterPlot(this.props.renderResults);
    return (
      <article className="uk-article">
        <p className="uk-article-meta">
          total vs correct
        </p>
        <Plot data={histData} layout={layout} config={{}} plotkey={'scatterplot1'} />
      </article>
    );
  }
}

export { Histogram3 };
