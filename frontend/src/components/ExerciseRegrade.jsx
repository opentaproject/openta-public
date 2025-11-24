import React from 'react';
import PropTypes from 'prop-types';

import { connect } from 'react-redux';
import { fetchRegradeTask, fetchExerciseRegradeResults } from '../fetchers';

import {} from '../actions';
import QMath from './QMath';

import immutable from 'immutable';
import moment from 'moment';

var unstableKey = 0;
const nextUnstableKey = () => unstableKey++;

const BaseExerciseRegradeResults = ({
  activeExercise,
  exerciseState,
  regradeAnswers,
  pending,
  exerciseKey,
  progress,
  preview,
  on_accept_regrade,
  regrade
}) => {
  {
    /* const getQuestionText = (key) => {
    const q = exerciseState
      .getIn([activeExercise, 'json', 'exercise', 'question'], immutable.List([]))
      .find((q) => q.getIn(['@attr', 'key']) === key, null);
    if (q) {
      return q.getIn(['text', '$']);
    }
    return '';
  };
  */
  }

  const getQuestionExpression = (key) => {
    var res = exerciseState.getIn([activeExercise, 'question', key, 'answer'], 'Click submit to see correct answer');
    return res;
  };

  {
    /* const getQuestionType = (key) => {
    const q = exerciseState
      .getIn([activeExercise, 'json', 'exercise', 'question'], immutable.List([]))
      .find((q) => q.getIn(['@attr', 'key']) === key, null);
    if (q) {
      return q.getIn(['@attr', 'type'], 'devLinearAlgebra');
    }
    return '';
  };
  */
  }

  const iconchoice = (b) => {
    var ret = 'uk-icon-question uk-text-danger';
    if (b == true) {
      ret = 'uk-icon uk-icon-check uk-text-success';
    } else if (b == false) {
      ret = 'uk-icon uk-icon-close uk-text-danger';
    }
    return ret;
  };

  const timeago = (t) => {
    var txt = moment(t).fromNow('mm');
    txt = txt.replace(/ *ago */, '');
    txt = txt.replace(/ *hours */, ' h');
    txt = txt.replace(/ *minutes* */, ' m');
    txt = txt.replace(/ a /, ' 1 ');
    txt = txt.replace(/ *seconds */, ' s');
    txt = txt.replace(/ *a few */, ' ~ 0 ');
    txt = txt.replace(/a/, ' 1 ');
    return txt;
  };

  var pprogress = progress + '%';
  var detail = preview == 'Cancelled' || preview == 'Done' || preview == 'Old Regrade' ? preview : '';
  var lines = preview.split('\n');
  lines.shift();
  var show_accept_and_reject = preview == 'Done' || preview == 'Old Regrade';
  var show_reject_only = preview == 'Cancelled'; // && ( ! finished )
  var show_accept_reject = !(detail == '') || preview == ''; // && ( ! finished )
  var ekey = String(exerciseKey);
  var waiting = progress == 0 && !show_accept_reject;
  show_reject_only = show_reject_only || preview == 'Done'; // && ( ! finished)
  var questions = exerciseState.getIn([activeExercise, 'json', 'exercise', 'question'], immutable.List([]));
  var texts = questions.map((q) => [q.getIn(['@attr', 'key']), q.getIn(['expression', '$'])]).toJS();
  var is_done = regradeAnswers.size > 0;
  var rg = regradeAnswers.filter((o) => o.size > 0);

  var dom = rg
    .map((regrade, question) => (
      <div key={'regrade' + question} className="uk-scrollable-box uk-margin-bottom" style={{ height: '70vh' }}>
        <div className="uk-align-center">
          {' '}
          <QMath
            questionType="devLinearAlgebra"
            exerciseKey={exerciseKey}
            expression={getQuestionExpression(question)}
          />{' '}
        </div>
        <table className="uk-table">
          <tbody>
            {regrade.map((answer) => (
              <tr key={nextUnstableKey()}>
                <td>
                  <div className="uk-text uk-text-small uk-text-primary">
                    {answer.get('username').replace(/@[^@]*/, '')}
                  </div>
                </td>
                <td className="uk-text-small">{timeago(answer.get('date'))}</td>
                <td
                  className={answer.get('new', false) ? 'uk-text-success' : 'uk-text-danger'}
                  title={answer.get('answer')}
                  data-uk-tooltip
                >
                  {answer.get('old') ? 'ok' : 'nok'} {'->'} {answer.get('new') ? 'ok' : 'nok'}
                  <i className={iconchoice(answer.get('new'))} />
                </td>
                <td>
                  <QMath questionType="linearAlgebra" exerciseKey={exerciseKey} expression={answer.get('answer')} />
                </td>
                <td>
                  <div className="uk-text uk-text-small">{answer.get('answer')}</div>
                </td>
                <td>{answer.get('error', '')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ))
    .toList();

  if (is_done && rg.size == 0) {
    dom = <div key={'regrade'}> No changes </div>;
  }

  var buttons = texts.map((b) => (
    <tr key={'butt3' + b[0]}>
      <td>
        <button key={'butt' + b[0]} className="uk-button uk-button-primary" onClick={() => regrade(ekey, b[0])}>
          Regrade key={b[0]}{' '}
        </button>{' '}
      </td>
      <td>
        {<QMath questionType="devLinearAlgebra" exerciseKey={exerciseKey} expression={getQuestionExpression(b[0])} />}
      </td>
    </tr>
  ));
  var show_regrade_buttons = progress == 'unstarted' || progress == 'finished';
  var show_progress_bar = !show_regrade_buttons;
  var show_dom = !show_regrade_buttons;
  if (false && rg.size == 0) {
    return buttons;
  } else {
    return (
      <div key={'rs' + nextUnstableKey()} className="uk-panel uk-width-1-1 uk-panel-box uk-margin-top">
        <h4 className="uk-panel-title uk-width-1-1">
          {show_regrade_buttons && (
            <table>
              <tbody>{buttons}</tbody>
            </table>
          )}
          {(true || (show_reject_only && !show_accept_and_reject)) && (
            <button className="uk-button uk-button-danger" onClick={() => on_accept_regrade(ekey, 'reset')}>
              {' '}
              Reset{' '}
            </button>
          )}
          {!show_accept_reject && (
            <button className="uk-button uk-button-danger" onClick={() => on_accept_regrade(ekey, 'cancel')}>
              {' '}
              Cancel{' '}
            </button>
          )}
        </h4>
        <h4>
          {waiting && <button className="uk-button "> Waiting </button>}
          {!pending && rg.size > 0 && (
            <div>
              <button className="uk-button uk-button-success" onClick={() => on_accept_regrade(ekey, 'yes')}>
                {' '}
                Accept{' '}
              </button>
              <button className="uk-button uk-button-danger" onClick={() => on_accept_regrade(ekey, 'no')}>
                {' '}
                Reject{' '}
              </button>
            </div>
          )}
        </h4>
        {pending && show_progress_bar && (
          <div className="uk-progress uk-width-1-1">
            <div className="uk-progress-bar" style={{ width: pprogress }}>
              <span className="uk-text-bold">{pprogress}</span>
            </div>
          </div>
        )}
        {pending && show_progress_bar && (
          <div>
            <h6 className="uk-width-1-1 uk-overflow-hidden">
              <table>
                <tbody>
                  {lines.map((line) => (
                    <tr key={'lis' + nextUnstableKey()}>
                      <td className="uk-overflow-hidden">{line}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </h6>
          </div>
        )}
        {show_dom && <div key={'dom' + nextUnstableKey()}> {dom} </div>}
      </div>
    );
  }
};

const mapDispatchToProps = (dispatch) => ({
  on_accept_regrade: (exercise, yesno) => {
    return dispatch(fetchRegradeTask(exercise, yesno));
  },
  regrade: (exercise, qkey) => dispatch(fetchExerciseRegradeResults(exercise, qkey))
});

const mapStateToProps = (state) => {
  var activeExercise = state.get('activeExercise');
  return {
    preview: state.getIn(['pendingState', 'regradePreview', activeExercise, 'preview'], ''),
    regradeAnswers: state.getIn(['results', 'exercises', activeExercise, 'regrade'], immutable.Map({})),
    pending: state.getIn(['pendingState', 'regradeResults', activeExercise], false),
    progress: state.getIn(['pendingState', 'regradeResults', activeExercise], 'unstarted'),
    pendingState: state.getIn(['pendingState'], immutable.Map({})),
    activeExercise: activeExercise,
    exerciseState: state.get('exerciseState'),
    exerciseKey: state.get('activeExercise')
  };
};

BaseExerciseRegradeResults.propTypes = {
  activeExercise: PropTypes.string,
  exerciseState: PropTypes.object,
  regradeAnswers: PropTypes.object,
  pending: PropTypes.oneOfType([PropTypes.number, PropTypes.bool, PropTypes.string]),
  exerciseKey: PropTypes.string,
  progress: PropTypes.oneOfType([PropTypes.number, PropTypes.string, PropTypes.bool]),
  preview: PropTypes.string,
  on_accept_regrade: PropTypes.func,
  regrade: PropTypes.func
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseExerciseRegradeResults);
