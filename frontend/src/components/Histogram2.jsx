import React, { Component } from 'react';
import PropTypes from 'prop-types';
import Plot from './Plot.jsx';

function generateHistPlot(renderResultsObject) {
  //{{{
  var j = renderResultsObject.toJS();
  var renderResults = j.sort( ( item1 , item2  ) => ( 
	  item1.n_passed_required + item1.n_passed_optional  + item1.n_passed_bonus -
	  ( item2.n_passed_required + item2.n_passed_optional  + item2.n_passed_bonus )) )
  var nrequired = renderResults
    .map((item) => item.n_passed_required ).reverse();
  var nbonus = renderResults
    .map((item) => item.n_passed_bonus).reverse();
  var noptional = renderResults
    .map((item) => item.n_passed_optional).reverse();
  var names = renderResults
    .map((item) => item.username).reverse() ;

  var x = Array.from( Array(renderResults.length).keys() )
  var maxReq = Math.max(...nrequired, 0) + 1;
  var maxBonus = Math.max(...nbonus, 0) + 1;
  var maxOptional = Math.max(...noptional, 0) + 1;

  var plotData = [];

  if (maxOptional != 1) {
    plotData.push({
      x: x,
      y: noptional,
      name: 'Optional',
      type: 'bar',
      marker: {
	      color: 'green',
      },
     hovertext: names ,
    });
  }

  if (maxBonus != 1) {
    plotData.push({
      x: x,
      y: nbonus,
      name: 'Bonus',
      type: 'bar',
      marker: {
	      color: 'orange',
      },
     hovertext: names ,
    });
  }


  if (maxReq != 1) {
    plotData.push({
      x: x ,
      y: nrequired,
      name: 'Obligatory',
      type: 'bar',
      marker: {
	      color: 'lightblue',
      },
      hovertext: names ,
    });
  }

  var layout = {
    barmode: 'stack',
    xaxis: {
      title: "Student",
    },
    yaxis: { title: 'Number completed ' },
    margin: {
      b: 80,
      t: 0,
      r: 0,
      h: 0
    }
  };
  return {
    data: plotData,
    layout: layout
  };
} //}}}

export default class Histogram2 extends Component {
  constructor() {
    super();
    this.state = { error: false };
  }

  static propTypes = {
    renderResults: PropTypes.object
  };

  render() {
    var { data: histData, layout: layout } = generateHistPlot(this.props.renderResults);
    return (
      <article className="uk-article">
        <p className="uk-article-meta">
          Specific number of exercises passed.
        </p>
        <Plot data={histData} layout={layout} config={{}} plotkey={'histplot1'} />
      </article>
    );
  }
}

export { Histogram2 };
