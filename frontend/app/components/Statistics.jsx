import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';

const BaseStatistics = ({ exerciseState }) => {
  var percent_complete = (exerciseState.get('percent_complete', 0)*100).toFixed(1) + '%';
  var percent_correct = (exerciseState.get('percent_correct', 0)*100).toFixed(1) + '%';
  var ncomplete = exerciseState.get('ncomplete', 0);
  var ncorrect = exerciseState.get('ncorrect', 0);
  var nstudents  = exerciseState.get('nstudents', 0);
  var nattempts  = exerciseState.get('mean_attempts', 0).toFixed(1);
  var deadline  = exerciseState.get('deadline', null);

  return (
    <div className="uk-panel uk-panel-box uk-margin-top">
    <article className="uk-article">
      <h1 className="uk-article-title">Statistics</h1>
      <dl className="uk-description-list-line">
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
          
        <dt><span className="uk-text-large"><span className="uk-text-bold">{ nattempts }</span> attempts per question (mean)</span></dt>
        <dd>
        </dd>
      </dl>
    </article>
    </div>
  );
}

const mapStateToProps = state => {
  var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));
  return {
  exerciseState: activeExerciseState,
};
}

const mapDispatchToProps = dispatch => ({
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseStatistics);


