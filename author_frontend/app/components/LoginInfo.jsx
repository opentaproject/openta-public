import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercises, 
  fetchExerciseXML,
  fetchExercise
} from '../fetchers.js';

import immutable from 'immutable';

const BaseLoginInfo = ({ username, admin }) => (
  <nav id="login" className="uk-nav uk-navbar-attached ta-nav">
  <div className="uk-container uk-container-center">
  <div className="uk-navbar-brand"><i className="uk-icon uk-icon-medium uk-icon-circle-o"></i><span className="uk-text-small uk-text-middle"> OpenTA</span></div>
  <div className="uk-navbar-flip">
  <ul className="uk-navbar-nav">
      <li>
      <a href="/logout/?next=/login"><i className="uk-icon uk-icon-sign-out uk-text-large uk-text-middle"></i></a>
      </li>
  </ul>
  </div>
  <div className="uk-navbar-content uk-navbar-center">
<i className={"uk-icon uk-text-success " + (admin ? "uk-icon-user-md" : "uk-icon-user")}></i> <span className="uk-text-large uk-text-middle">{username}</span>{ admin ? ( <span className="uk-text-small uk-text-middle"> (admin)</span> ) : "" }
</div>
  </div>
  </nav>
);

BaseLoginInfo.propTypes = {
  username: PropTypes.string,
  admin: PropTypes.bool
};

const mapStateToProps = state => {
  return ({
  username: state.getIn(['login', 'username']),
  admin: state.getIn(['login', 'admin'])
});
}

export default connect(mapStateToProps)(BaseLoginInfo)
