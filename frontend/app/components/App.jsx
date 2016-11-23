import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import Counter from './Counter';
import ExerciseList from './ExerciseList';
import Exercise from './Exercise';
import AuthorExercise from './AuthorExercise';
import LoginInfo from './LoginInfo';
import Course from './Course';
import immutable from 'immutable';

class BaseApp extends React.Component {
  static propTypes = {
    admin: PropTypes.bool,
    author: PropTypes.bool,
    view: PropTypes.bool,
    activeExercise: PropTypes.string
  };
  render() {
    return (
      <div>
        <LoginInfo/>
        <div id="content" className="">
          <div id="main" className="uk-grid">
            <div className="uk-container-center uk-flex uk-flex-center uk-width-1-1">
              { /*this.props.activeExercise === "" && <div className="uk-width-medium-1-6"/>*/ }
              { this.props.activeExercise === "" && <div className="uk-width-medium-2-3 uk-margin-small-left"><Course/></div> }  
              { /*(this.props.admin || this.props.author) ? <span/> : <div className="exercise-spacing"></div> */ }
              { this.props.activeExercise !== "" &&
              <div className="exercise-list">
                <ExerciseList />               
              </div>
              }
              { this.props.activeExercise === "" ? (<span/>) : ((this.props.author || this.props.admin || this.props.view) ? <AuthorExercise /> : <div className="exercise uk-padding-remove"><Exercise/></div>) }
            </div>
          </div>
        </div>
      </div>
    );
  }
}

const mapStateToProps = state => ({
  admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
  author: state.getIn(['login', 'groups'],immutable.List([])).includes('Author'),
  view: state.getIn(['login', 'groups'],immutable.List([])).includes('View'),
  activeExercise: state.get('activeExercise')
});

export default connect(mapStateToProps)(BaseApp)
