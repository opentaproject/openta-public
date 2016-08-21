import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercises, 
  fetchExerciseXML,
  fetchExercise
} from '../fetchers.js';

import immutable from 'immutable';

const BaseLoginInfo = ({ username }) => (
  <nav id="login" className="uk-nav uk-navbar-attached ta-nav">
  <div className="uk-container uk-container-center">
  <div className="uk-navbar-brand"><i className="uk-icon uk-icon-medium uk-icon-circle-o"></i><span className="uk-text-small uk-text-middle"> OpenTA</span></div>
  <div className="uk-navbar-flip">
  <ul className="uk-navbar-nav">
      <li>
      <a href="/logout"><i className="uk-icon uk-icon-sign-out uk-text-large uk-text-middle"></i></a>
      </li>
  </ul>
  </div>
  <div className="uk-navbar-content uk-navbar-center">
<i className="uk-icon uk-icon-user uk-text-success"></i> <span className="uk-text-large uk-text-middle">{username}</span>
</div>
  </div>
  </nav>
);

BaseLoginInfo.propTypes = {
  username: PropTypes.string
};

const mapStateToProps = state => ({
  username: state.getIn(['login', 'username'])
});

export default connect(mapStateToProps)(BaseLoginInfo)
