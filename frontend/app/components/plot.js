import plotly from 'plotly.js/lib/core';
plotly.register([
    require('plotly.js/lib/histogram'),
    require('plotly.js/lib/bar'),
    require('plotly.js/lib/histogram2d'),
]);
export default plotly
