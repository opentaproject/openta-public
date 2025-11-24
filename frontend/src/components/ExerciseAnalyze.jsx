import React from 'react';
import PropTypes from 'prop-types';

import { connect } from 'react-redux';
import { fetchAnalyzeTask, fetchExerciseAnalyzeResults } from '../fetchers';

import {} from '../actions';
import QMath from './QMath';

import immutable from 'immutable';
import moment from 'moment';

var unstableKey = 0;
const nextUnstableKey = () => unstableKey++;

const BaseExerciseAnalyzeResults = ({
  activeExercise,
  exerciseState,
  analyzeAnswers,
  pending,
  exerciseKey,
  progress,
  preview,
  on_accept_analyze,
  analyze
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
  var detail = preview == 'Cancelled' || preview == 'Done' || preview == 'Old Analyze' ? preview : '';
  var lines = preview.split('\n');
  lines.shift();
  var show_accept_and_reject = preview == 'Done' || preview == 'Old Analyze';
  var show_reject_only = preview == 'Cancelled'; // && ( ! finished )
  var show_accept_reject = !(detail == '') || preview == ''; // && ( ! finished )
  var ekey = String(exerciseKey);
  var waiting = progress == 0 && !show_accept_reject;
  show_reject_only = show_reject_only || preview == 'Done'; // && ( ! finished)
  var questions = exerciseState.getIn([activeExercise, 'json', 'exercise', 'question'], immutable.List([]));
  var texts = questions.map((q) => [q.getIn(['@attr', 'key']), q.getIn(['expression', '$'])]).toJS();
  var is_done = analyzeAnswers.size > 0;
  var rg = analyzeAnswers
  var dataObject = rg.toJS();
  const dataArray = Object.entries(dataObject)
    .sort(([keyA], [keyB]) => keyA.localeCompare(keyB)) // Sort numerically
    .map(([key, item]) => ({ id: key, ...item })); //
  var dom = dataArray.map((item) => (
        <li key={item.id}>
	  <strong>  {item.count}    </strong> {item.qtype}   {item.answer_data} [ { item.c } ]
        </li>
      ))


  //var rgg =  rg.toJS() 
  //console.log("INDEX 5 = ", rgg[5] )
  //for( let i = 0; i <  10 ; i++ ){
  //	  console.log("I =}")
  //}
//var dom = rg.map((item,index) => (
 //             <li className="uk-text uk-text-small uk-text-primary" key={index}> { String( item  ) }   </li>
  //          ))


  var buttons = texts.map((b) => (
    <tr key={'butt3' + b[0]}>
      <td>
        <button key={'butt' + b[0]} className="uk-button uk-button-primary" onClick={() => analyze(ekey, b[0])}>
          Analyze key={b[0]}{' '}
        </button>{' '}
      </td>
      <td>
        {<QMath questionType="devLinearAlgebra" exerciseKey={exerciseKey} expression={getQuestionExpression(b[0])} />}
      </td>
    </tr>
  ));
  var show_analyze_buttons = progress == 'unstarted' || progress == 'finished';
  var show_progress_bar = !show_analyze_buttons;
  var show_dom = !show_analyze_buttons;
  if (false && rg.size == 0) {
    return buttons;
  } else {
    return (
      <div key={'rs' + nextUnstableKey()} className="uk-panel uk-width-1-1 uk-panel-box uk-margin-top">
        <h4 className="uk-panel-title uk-width-1-1">
          {show_analyze_buttons && (
            <table>
              <tbody>{buttons}</tbody>
            </table>
          )}
          {(true || (show_reject_only && !show_accept_and_reject)) && (
            <button className="uk-button uk-button-danger" onClick={() => on_accept_analyze(ekey, 'reset')}>
              {' '}
              Reset{' '}
            </button>
          )}
          {!show_accept_reject && (
            <button className="uk-button uk-button-danger" onClick={() => on_accept_analyze(ekey, 'cancel')}>
              {' '}
              Cancel{' '}
            </button>
          )}
        </h4>
        <h4>
          {waiting && <button className="uk-button "> Waiting </button>}
          {!pending && rg.size > 0 && (
            <div>
              <button className="uk-button uk-button-success" onClick={() => on_accept_analyze(ekey, 'yes')}>
                {' '}
                Accept{' '}
              </button>
              <button className="uk-button uk-button-danger" onClick={() => on_accept_analyze(ekey, 'no')}>
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
        {show_dom && <div key={'dom' + nextUnstableKey()}> <ul> {dom} </ul> </div>}
      </div>
    );
  }
};

const mapDispatchToProps = (dispatch) => ({
  on_accept_analyze: (exercise, yesno) => {
    return dispatch(fetchAnalyzeTask(exercise, yesno));
  },
  analyze: (exercise, qkey) => dispatch(fetchExerciseAnalyzeResults(exercise, qkey))
});

const mapStateToProps = (state) => {
  var activeExercise = state.get('activeExercise');
  return {
    preview: state.getIn(['pendingState', 'analyzePreview', activeExercise, 'preview'], ''),
    analyzeAnswers: state.getIn(['results', 'exercises', activeExercise, 'analyze'], immutable.Map({})),
    pending: state.getIn(['pendingState', 'analyzeResults', activeExercise], false),
    progress: state.getIn(['pendingState', 'analyzeResults', activeExercise], 'unstarted'),
    pendingState: state.getIn(['pendingState'], immutable.Map({})),
    activeExercise: activeExercise,
    exerciseState: state.get('exerciseState'),
    exerciseKey: state.get('activeExercise')
  };
};

BaseExerciseAnalyzeResults.propTypes = {
  activeExercise: PropTypes.string,
  exerciseState: PropTypes.object,
  analyzeAnswers: PropTypes.object,
  pending: PropTypes.oneOfType([PropTypes.number, PropTypes.bool, PropTypes.string]),
  exerciseKey: PropTypes.string,
  progress: PropTypes.oneOfType([PropTypes.number, PropTypes.string, PropTypes.bool]),
  preview: PropTypes.string,
  on_accept_analyze: PropTypes.func,
  analyze: PropTypes.func
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseExerciseAnalyzeResults);
