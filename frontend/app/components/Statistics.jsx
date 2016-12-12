import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Plot from './Plot.jsx';
import Spinner from './Spinner.jsx';
import moment from 'moment';

const BaseStatistics = ({ exerciseState, pendingState, statistics }) => {
  var percent_complete = (exerciseState.get('percent_complete', 0)*100).toFixed(1) + '%';
  var percent_correct = (exerciseState.get('percent_correct', 0)*100).toFixed(1) + '%';
  var percent_tried = (exerciseState.get('percent_tried', 0)*100).toFixed(1) + '%';
  var ntried = exerciseState.get('ntried', 0);
  var ncomplete = exerciseState.get('ncomplete', 0);
  var ncorrect = exerciseState.get('ncorrect', 0);
  var nstudents  = exerciseState.get('nstudents', 0);
  var nattempts_mean  = exerciseState.get('attempts_mean', 0).toFixed(1);
  var nattempts_median  = exerciseState.get('attempts_median', 0).toFixed(1);
  var deadline  = exerciseState.get('deadline', null);

  var formatDate = date => moment(date).format('YYYY-MM-DD HH:mm:ss');
  var formatTimestamp = date => moment(date, 'X').format('YYYY-MM-DD HH:mm:ss');

  //var activityHistogram = exerciseState.getIn(['activity', 'answers'], immutable.List([])).map(formatDate).toArray();
  //console.dir(activityHistogram)
  var y = exerciseState.getIn(['activity', 'answers_histogram'], immutable.List([])).toArray();
  var x = exerciseState.getIn(['activity', 'bins'], immutable.List([])).butLast().map(formatTimestamp).toArray();

  var plotData = [ {
    y: y,
    x: x,
    type: "bar",
  },];
  var shapes = []
  if(deadline) {
    var deadlinePlotly = moment(deadline).format('YYYY-MM-DD HH:mm:ss');
    shapes.push(
    {
      type: 'line',
      yref: 'paper',
      'x0': deadlinePlotly,
      'y0': 0,
      'x1': deadlinePlotly,
      'y1': 1,
      'opacity': 0.6,
      'line': {
        'color': 'rgb(255,0,0)',
        'dash': 'dashdot',
        'width': 1.5
      },
    });
  }
  
  var layout = {
  title: "Activity", 
  xaxis: {
  }, 
  yaxis: {title: "Tries/2h"},
  shapes: shapes,
  };

  return (
    <div className="uk-panel uk-panel-box uk-margin-top">
    <article className="uk-article">
      <h1 className="uk-article-title">Statistics</h1>
      <dl className="uk-description-list-line">
        <dt>
          <span className="uk-text-bold uk-text-large">{ntried}/{nstudents}</span>
          <span> tried this exercise.</span>
        </dt>
        <dd>
          <div className="uk-progress uk-progress-warning">
          <div className="uk-progress-bar" style={{'width': percent_tried}}><span className="uk-text-bold">{percent_tried}</span></div>
          </div>
        </dd>
        <dt>
          <span className="uk-text-bold uk-text-large">{ncorrect}/{nstudents}</span>
          <span> answered correctly.</span>
        </dt>
        <dd>
          <div className="uk-progress">
          <div className="uk-progress-bar" style={{'width': percent_correct}}><span className="uk-text-bold">{percent_correct}</span></div>
          </div>
        </dd>
        { deadline &&
        <dt>
          <span className="uk-text-bold uk-text-large">{ncomplete}/{nstudents}</span>
          <span> complete (correct before deadline and image).</span>
        </dt>
        }
        { deadline &&
        <dd>
          <div className="uk-progress uk-progress-success">
          <div className="uk-progress-bar" style={{'width': percent_complete}}><span className="uk-text-bold">{percent_complete}</span></div>
          </div>
        </dd>
        }
          
        <dt><span className="uk-text-large"><span className="uk-text-bold">{ nattempts_median }</span> attempts per question (median)</span></dt>
        <dd>
        </dd>
        <dt></dt>
        <dd>
         { !pendingState.getIn(['statistics']) && <Plot key="statistics-plot" data={plotData} layout={layout} config={{}}/> }
         { pendingState.getIn(['statistics']) && <Spinner/> }
        </dd> 
      </dl>
    </article>
    </div>
  );
}

const mapStateToProps = state => {
  var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));
  var pendingState = state.getIn(['pendingState','exercise',state.get('activeExercise')], immutable.Map({}));
  return {
  exerciseState: activeExerciseState,
  pendingState: pendingState,
  statistics: state.get('statistics'),
};
}

const mapDispatchToProps = dispatch => ({
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseStatistics);
