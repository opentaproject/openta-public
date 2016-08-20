import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercises, 
  fetchExerciseXML,
  fetchExercise
} from '../fetchers.js';

import immutable from 'immutable';

const BaseLoginInfo = ({ username }) => (
  <div>
    Username: {username}
  </div>
);

BaseLoginInfo.propTypes = {
  username: PropTypes.string
};

const mapStateToProps = state => ({
  username: state.getIn(['login', 'username'])
});

export default connect(mapStateToProps)(BaseLoginInfo)
