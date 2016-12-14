import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import Counter from './Counter';
import ExerciseList from './ExerciseList';
import Exercise from './Exercise';
import AuthorExercise from './AuthorExercise';
import LoginInfo from './LoginInfo';
import Course from './Course';
import Results from './Results';
import ReloadExercises from './ReloadExercises';
import immutable from 'immutable';
import { menuPositionAt, menuPositionUnder } from '../menu.js';

class BaseApp extends React.Component {
  static propTypes = {
    admin: PropTypes.bool,
    author: PropTypes.bool,
    view: PropTypes.bool,
    activeExercise: PropTypes.string,
    menuPath: PropTypes.object
  };
  render() {
    return (
      <div className="uk-grid">
        <div className="uk-width-1-1"><LoginInfo/></div>
        <div id="content" className="uk-width-1-1">
          <div id="main" className="uk-grid">
            <div className="uk-container-center uk-flex uk-flex-center uk-width-1-1">
              { /*this.props.activeExercise === "" && <div className="uk-width-medium-1-6"/>*/ }
              { (
                menuPositionUnder(this.props.menuPath, ['exercises', 'activity']) || 
                menuPositionAt(this.props.menuPath, ['exercises']) || 
                menuPositionAt(this.props.menuPath, [])) &&
                <div className="uk-width-medium-2-3 uk-margin-small-left"><Course/></div> }  
              { menuPositionUnder(this.props.menuPath, ['results']) && <div className="uk-width-medium-2-3 uk-margin-small-left"><Results/></div> }  
              { menuPositionAt(this.props.menuPath, ['exercises', 'reload']) && <div className="uk-width-medium-2-3 uk-margin-small-left"><ReloadExercises/></div> }  
              { /*(this.props.admin || this.props.author) ? <span/> : <div className="exercise-spacing"></div> */ }
              { menuPositionUnder(this.props.menuPath, ['activeExercise']) &&
              <div className="exercise-list">
                <ExerciseList />               
              </div>
              }
              { menuPositionUnder(this.props.menuPath, ['activeExercise']) && ((this.props.author || this.props.admin || this.props.view) ? <AuthorExercise /> : <div className="exercise uk-padding-remove"><Exercise/></div>) }
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
  activeExercise: state.get('activeExercise'),
  menuPath: state.get('menuPath')
});

export default connect(mapStateToProps)(BaseApp)
