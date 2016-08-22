import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import Counter from './Counter';
import ExerciseList from './ExerciseList';
import Exercise from './Exercise';
import AuthorExercise from './AuthorExercise';
import LoginInfo from './LoginInfo';
import Course from './Course';

class BaseApp extends React.Component {
  static propTypes = {
    login: PropTypes.object
  };
  render() {
    return (
      <div>
      <LoginInfo/>
      <div id="content" className="uk-container uk-container-center">
        <div id="main" className="uk-grid">
        { /* <ExerciseList /> */ }
          <div className="uk-width-medium-5-6">
          <Course/>
          { /*this.props.admin ? <AuthorExercise /> : <Exercise/>*/ }
          </div>
        </div>
      </div>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  admin: state.getIn(['login', 'admin'])
});

export default connect(mapStateToProps)(BaseApp)
