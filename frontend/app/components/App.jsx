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
    admin: PropTypes.bool,
    activeExercise: PropTypes.string
  };
  render() {
    return (
      <div>
        <LoginInfo/>
        <div id="content" className={this.props.admin ? "" : "uk-container uk-container-center"}>
          <div id="main" className="uk-grid">
            <div className={"uk-container-center uk-grid " + (this.props.admin ? "uk-width-medium-1-1" : "uk-width-large-4-6")}>
              { this.props.activeExercise === "" && <div className="uk-width-1-1"><Course/></div> }  
              <div className={this.props.admin ? "uk-width-medium-1-6" : "uk-width-large-2-10 uk-width-medium-1-4"}>
              { this.props.activeExercise !== "" ? <ExerciseList /> : "" }
              </div>
              <div className={this.props.admin ? "uk-width-medium-5-6" : "uk-width-large-6-10 uk-width-medium-3-4"}>
              { this.props.activeExercise === "" ? (<span/>) : (this.props.admin ? <AuthorExercise /> : <Exercise/>) }
              </div>
              { !this.props.admin && <div className="uk-width-medium-2-10"/> }
            </div>
          </div>
        </div>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  admin: state.getIn(['login', 'admin']),
  activeExercise: state.get('activeExercise')
});

export default connect(mapStateToProps)(BaseApp)
