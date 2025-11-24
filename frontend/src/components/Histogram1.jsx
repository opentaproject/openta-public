import React, { Component } from 'react';
import PropTypes from 'prop-types';
import Plot from './Plot.jsx';

function generateHistPlot(renderResultsObject) {
  //{{{
  var j = renderResultsObject.toJS();
  var renderResults = j.sort( ( item2 , item1  ) => ( item1.n_passed_total  -   item2.n_passed_total  ) )
  var requiredHistogram = renderResults
    .map((item) => item.n_passed_required )
    .filter((item) => item > 0);
  var bonusHistogram = renderResults
    .map((item) => item.n_passed_bonus)
    .filter((item) => item > 0);
  var optionalHistogram = renderResults
    .map((item) => item.n_passed_optional)
    .filter((item) => item > 0);
  var xbins = [];
  var maxReq = Math.max(...requiredHistogram, 0) + 1;
  var maxBonus = Math.max(...bonusHistogram, 0) + 1;
  var maxOptional = Math.max(...optionalHistogram, 0) + 1;
  var len = Math.max(maxReq, maxBonus, maxOptional);
  for (var i = 0; i < len; i++) {
    if (optionalHistogram.includes(i) || requiredHistogram.includes(i) || bonusHistogram.includes(i)) {
      xbins.push(i);
    }
  }

  var plotData = [];
  if (maxReq != 1) {
    plotData.push({
      x: requiredHistogram,
      name: 'Obligatory',
      type: 'histogram'
    });
  }
  if (maxBonus != 1) {
    plotData.push({
      x: bonusHistogram,
      name: 'Bonus',
      type: 'histogram'
    });
  }
  if (maxOptional != 1) {
    plotData.push({
      x: optionalHistogram,
      name: 'Optional',
      type: 'histogram'
    });
  }

  var layout = {
    bargroupgap: 0.2,
    barmode: 'group',
    xaxis: xbins,
    //xaxis: {
    //  title: "Number of exercises",
    //  tickmode: "linear",
    //},
    yaxis: { title: 'Number of students' },
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

export default class Histogram1 extends Component {
  constructor() {
    super();
    this.state = { error: false };
  }

  static propTypes = {
    renderResults: PropTypes.object
  };

  render() {
    var { data: histData, layout: histLayout } = generateHistPlot(this.props.renderResults);
    return (
      <article className="uk-article">
        <p className="uk-article-meta">
          Number of students that have passed specific number of obligatory and bonus exercises.
        </p>
        <Plot data={histData} layout={histLayout} config={{}} plotkey={'histplot1'} />
      </article>
    );
  }
}

export { Histogram1 };
