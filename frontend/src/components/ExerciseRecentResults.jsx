import React from 'react';
import { connect } from 'react-redux';
import QMath from './QMath';
import KatexSpan from './KatexSpan';

import immutable from 'immutable';
import moment from 'moment';
import { asciiMathToMathJS } from './mathrender/string_parse';

function createMarkup(value) {
  try {
    var rvalue = katex.renderToString(value);
    return { __html: rvalue };
  } catch (e) {
    return { __html: value };
  }
}

function renderExpression(expression) {
  try {
    var preParsed = asciiMathToMathJS(expression);
    return '$' + mathjs.parse(preParsed.out).toTex() + '$';
  } catch (e) {
    return expression;
  }
}

const BaseExerciseRecentResults = ({ activeExercise, exerciseState, recentAnswers, pending, admin, exerciseKey }) => {
  const getQuestionText = (key) => {
    const q = exerciseState
      .getIn([activeExercise, 'json', 'exercise', 'question'], immutable.List([]))
      .find((q) => q.getIn(['@attr', 'key']) === key, null);
    if (q) {
      return q.getIn(['text', '$']);
    }
    return '';
  };

  const getQuestionType = (key) => {
    const q = exerciseState
      .getIn([activeExercise, 'json', 'exercise', 'question'], immutable.List([]))
      .find((q) => q.getIn(['@attr', 'key']) === key, null);
    if (q) {
      return q.getIn(['@attr', 'type'], 'devLinearAlgebra');
    }
    return '';
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

  var questions = recentAnswers.keys();
  // console.log("QUESTIONS = ", questions)
  return (
    <div className="uk-panel uk-panel-box uk-margin-top">
      <h3 className="uk-panel-title">Recent answers by students</h3>
      <div className="uk-scrollable-box uk-margin-bottom" style={{ height: '70vh' }}>
        <table className="uk-table uk-table-condensed">
          <thead>
            <tr>
              {recentAnswers
                .map((users, question) => (
                  <th key={question} style={{ maxWidth: '300px' }}>
                    {' '}
                    <KatexSpan message={getQuestionText(question)} />
                  </th>
                ))
                .toList()}
            </tr>
          </thead>
          <tbody>
            <tr>
              {recentAnswers
                .map((users, question) => (
                  <td key={question}>
                    {users
                      .map((data) => (
                        <div className="uk-panel uk-panel-box uk-margin-small-top" key={data.get('pk')}>
                          {admin && (
                            <div>
                              {' '}
                              <span className="uk-panel-title">{data.get('username')} </span>
                              <span>
                                {' '}
                                {data.get('n_answers')} &nbsp; answers {getQuestionType(question)}{' '}
                              </span>{' '}
                            </div>
                          )}
                          <table className="uk-table" style={{ width: 'auto' }}>
                            <tbody>
                              {data.get('answers').map((answer) => (
                                <tr key={answer.get('question') + ':' + answer.get('user') + ':' + answer.get('date')}>
                                  <td
                                    className={answer.get('correct', false) ? 'uk-text-success' : 'uk-text-danger'}
                                    title={answer.get('answer')}
                                    data-uk-tooltip
                                  >
                                    <i
                                      className={
                                        answer.get('correct', false)
                                          ? 'uk-icon uk-icon-check uk-text-success'
                                          : 'uk-icon uk-icon-close uk-text-danger'
                                      }
                                    />
                                  </td>
                                  <td className="uk-text-small"> {timeago(answer.get('date'))} </td>

                                  {!('textbased' == getQuestionType(question)) && (
                                    <td>
                                      {' '}
                                      {
                                        <QMath
                                          questionType="linearAlgebra"
                                          exerciseKey={exerciseKey}
                                          expression={answer.get('answer')}
                                        />
                                      }{' '}
                                    </td>
                                  )}
                                  <td></td>
                                  <td>
                                    <div className="uk-text uk-text-small">
                                      <KatexSpan message={answer.get('answer')} />
                                    </div>
                                  </td>
                                </tr>
                              ))}
                              {!('textbased' == getQuestionType(question)) &&
                                data.get('n_answers') > data.get('answers').size && (
                                  <tr key="last">
                                    <td className="uk-text-center">
                                      <i className="uk-icon uk-icon-ellipsis-v" />
                                    </td>
                                    <td />
                                  </tr>
                                )}
                            </tbody>
                          </table>
                        </div>
                      ))
                      .toList()}
                  </td>
                ))
                .toList()}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

const mapStateToProps = (state) => {
  var activeExercise = state.get('activeExercise');
  return {
    recentAnswers: state.getIn(['results', 'exercises', activeExercise, 'recent'], immutable.Map({})),
    pending: state.getIn(['pendingState', 'results', 'exercises', activeExercise, 'recent'], false),
    activeExercise: activeExercise,
    exerciseState: state.get('exerciseState'),
    exerciseKey: state.get('activeExercise'),
    admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin')
  };
};

const mapDispatchToProps = (dispatch) => ({});

export default connect(mapStateToProps, mapDispatchToProps)(BaseExerciseRecentResults);
