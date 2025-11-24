import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import Alert from './Alert.jsx';
import immutable from 'immutable';
import { SUBPATH, language_code } from '../settings.js';
import { getcookie } from '../cookies.js';
import Cookies from 'universal-cookie';

import {
  fetchExercise,
  fetchExerciseRemoteState,
  fetchSameFolder,
  fetchExerciseTree
} from '../fetchers.js';


import { fetchSetSelectedExercises } from '../fetchers/exercise.js';

var unstableKey = 0;
const nextUnstableKey = () => unstableKey++;

class BaseEditExericseOptions extends Component {
  constructor(props) {
    super();
    this.state = {};
  }

  static propTypes = {
    activeAdminTool: PropTypes.string,
    admin: PropTypes.bool,
    author: PropTypes.bool,
    view: PropTypes.bool
  };

  handleIframeLoad = (event, onOptionsSubmit, onOptionsLoad) => {
    var submitted_cookie = getcookie('submitted', event.target.contentDocument);
    if (submitted_cookie.length > 0 && submitted_cookie[0] === 'true') {
	var cookies = new Cookies();
	cookies.set('submitted', 'false', { path: '/', secure: true, sameSite: 'none'  });
     	this.props.onOptionsSubmit();
    }
    onOptionsLoad(this.props.selectedExercises);
  };

  render() {
    var key = null;
    //if ( this.props.exerciseState ){
    //   var key =  this.props.exerciseState.exerciseKey
    //  }
    if (this.props.selectedExercises.length > 0) {
      var key = this.props.selectedExercises[0];
    }
    if (this.props.exerciseKey) {
      var key = this.props.exerciseKey;
    }
    if (key == null) {
      return (
        <div>
          <Alert type="error">{'No exercise selected!'}</Alert>
        </div>
      );
    }
    var exerciseState = this.props.exerciseState;
    var pendingState = this.props.pendingState;
    var fields = [
      'name',
      'published',
      'type',
      'deadline',
      'image',
      'allow_pdf',
      'student_assets',
      'solution',
      'feedback'
    ];
    var selectedExercisesMeta = this.props.selectedExercisesMeta;
    //console.log("selectedExercisesMeta = ", selectedExercisesMeta)
    var lang = this.props.lang;
    var ok_lang = language_code.indexOf(lang) !== -1;

    var nrendered = selectedExercisesMeta.map((item) => (
      <tr key={nextUnstableKey() + 'aex'}>
        <td>{item.name}</td>
        <td>{item.published ? 'yes' : 'no'}</td>
        <td>{item.type}</td>
        <td>{item.deadline ? item.deadline : 'none'}</td>
        <td>{item.image ? 'yes' : 'no'}</td>
        <td>{item.allow_pdf ? 'yes' : 'no'}</td>
        <td>{item.student_assets ? 'yes' : 'no'}</td>
        <td>{item.solution ? 'yes' : 'no'}</td>
        <td>{item.feedback ? 'yes' : 'no'}</td>
      </tr>
    ));
    var greenBorder = {
      borderColor: 'rgb(0,221,0)',
      borderWidth: '2px',
      borderStyle: 'solid'
    };

    var fields = [
      'name',
      'published',
      'type',
      'deadline',
      'image',
      'allow_pdf',
      'student_assets',
      'solution',
      'feedback'
    ];
    var tabledom =
      nrendered.length > 0 ? (
        <table className="uk-table uk-table-condensed uk-text-warning uk-text-small" style={greenBorder}>
          <tbody>
            <tr>
              <th>Exercise </th>
              <th>published</th>
              <th>type</th>
              <th>deadline</th>
              <th>image</th>
              <th>pdf</th>
              <th>assets</th>
              <th>solution</th>
              <th>feedback</th>
            </tr>
            {nrendered}
          </tbody>
        </table>
      ) : (
        ''
      ); // 'No others'
    var lang_dom = ok_lang ? (
      ''
    ) : (
      <div className="uk-text uk-text-large uk-badge uk-badge-danger">
        {' '}
        Language for options edit should be {language_code}{' '}
      </div>
    );
    var authorDOM = (
      <div className="uk-panel uk-panel-box uk-panel-box-secondary uk-margin-top">
        {lang_dom}
        {tabledom}
        <iframe
          key={'edit-meta' + key}
          scrolling="no"
          className="options"
          src={SUBPATH + '/exercise/' + key + '/editmeta'}
          onLoad={(event) => this.handleIframeLoad(event, this.props.onOptionsSubmit, this.props.onOptionsLoad)}
	  onSubmit={(event) => this.handleIframeLoad(event, this.props.onOptionsSubmit, this.props.onOptionsLoad)}
        />
      </div>
    );
    return key ? authorDOM : <span />;
  }
}

function handleOptionsSubmit() {
  return (dispatch, getState) => {
    var coursePk = getState().get('activeCourse');
    var subdomain = getState().get('subdomain');
    var exercise = getState().get('activeExercise');
    dispatch(fetchExercise(exercise, true));
    dispatch(fetchExerciseRemoteState(exercise));
    dispatch(fetchSameFolder(exercise, subdomain));
    dispatch(fetchExerciseTree(coursePk));
  };
}

const mapStateToProps = (state) => {
  //var activeExerciseState = _.get(state.exerciseState, state.activeExercise, {});
  var activeExerciseState = state.getIn(['exerciseState', state.get('activeExercise')], immutable.Map({}));
  return {
    exerciseState: activeExerciseState,
    activeAdminTool: state.get('activeAdminTool'),
    admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
    author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
    view: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
    exercises: state.getIn(['exerciseState'], immutable.List([])),
    selectedExercises: state.getIn(['selectedExercises'], immutable.List([])),
    selectedExercisesMeta: state.getIn(['selectedExercisesMeta'], immutable.List([])),
    lang: state.getIn(['lang'], null)
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    onOptionsSubmit: () => { 
	    	dispatch(handleOptionsSubmit()) } ,
    onOptionsLoad: (exercises) => dispatch(fetchSetSelectedExercises(exercises))
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseEditExericseOptions);
