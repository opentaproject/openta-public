import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import ExerciseList from './ExerciseList';
import StudentExercise from './StudentExercise';
import AuthorExercise from './AuthorExercise';
import LoginInfo from './LoginInfo';
import Course from './Course';
import CourseOptions from './CourseOptions';
import CourseExercisesImport from './CourseExercisesImport';
import CourseExercisesExport from './CourseExercisesExport';
import CourseExport from './CourseExport';
import CourseDuplicate from './CourseDuplicate';
import ServerImport from './ServerImport';
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
    menuPath: PropTypes.object,
  };
  render() {
    return (
      <div className="uk-grid">
        <div className="uk-width-1-1"><LoginInfo /></div>
        <div id="content" className="uk-width-1-1">
          <div id="main" className="uk-grid uk-margin-remove">
            <div className="uk-container-center uk-flex uk-flex-center uk-width-1-1">
              { /*this.props.activeExercise === "" && <div className="uk-width-medium-1-6"/>*/}
              {(
                menuPositionUnder(this.props.menuPath, ['exercises', 'activity']) ||
                menuPositionAt(this.props.menuPath, ['exercises']) ||
                menuPositionAt(this.props.menuPath, [])) &&
                <div className="uk-width-medium-4-5 uk-margin-small-left"><Course /></div>}
              {menuPositionUnder(this.props.menuPath, ['results']) && <div className="uk-width-1-1 uk-margin-small-left results"><Results /></div>}
              {menuPositionUnder(this.props.menuPath, ['course', 'options']) && <div className="uk-width-1-1 uk-margin-small-left"><CourseOptions /></div>}
              {menuPositionUnder(this.props.menuPath, ['course', 'import_exercises']) && <div className="uk-width-1-1 uk-margin-small-left"><CourseExercisesImport /></div>}
              {menuPositionUnder(this.props.menuPath, ['course', 'export_exercises']) && <div className="uk-width-1-1 uk-margin-small-left"><CourseExercisesExport /></div>}
              {menuPositionUnder(this.props.menuPath, ['course', 'export']) && <div className="uk-width-1-1 uk-margin-small-left"><CourseExport /></div>}
              {menuPositionUnder(this.props.menuPath, ['course', 'duplicate']) && <div className="uk-width-1-1 uk-margin-small-left"><CourseDuplicate action='duplicate'/></div>}
              {menuPositionUnder(this.props.menuPath, ['course', 'modify']) && <div className="uk-width-1-1 uk-margin-small-left"><CourseDuplicate action='modify'/></div>}
              {menuPositionUnder(this.props.menuPath, ['server', 'import']) && <div className="uk-width-1-1 uk-margin-small-left"><ServerImport /></div>}
              {menuPositionAt(this.props.menuPath, ['exercises', 'reload']) && <div className="uk-width-medium-2-3 uk-margin-small-left"><ReloadExercises /></div>}
              { /*(this.props.admin || this.props.author) ? <span/> : <div className="exercise-spacing"></div> */}
              {menuPositionUnder(this.props.menuPath, ['activeExercise']) &&
                <div className="exercise-list">
                  <ExerciseList showOnCanvas={false} />
                </div>
              }
              {menuPositionUnder(this.props.menuPath, ['activeExercise']) && (((this.props.author || this.props.admin || this.props.view) && !menuPositionUnder(this.props.menuPath, ['activeExercise', 'student'])) ? <AuthorExercise /> : <div className="exercise uk-padding-remove"><StudentExercise /></div>)}
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
  student: state.getIn(['login', 'groups'],immutable.List([])).includes('Student'),
  activeExercise: state.get('activeExercise'),
  menuPath: state.get('menuPath'),
  lti_login: state.getIn(['login','lti_login'] , true)
});

export default connect(mapStateToProps)(BaseApp)
