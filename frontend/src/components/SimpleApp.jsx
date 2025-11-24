import React from 'react';
import StudentExercise from './StudentExercise';
import immutable from 'immutable';

class BaseApp extends React.Component {
  static propTypes = {
    admin: PropTypes.bool,
    author: PropTypes.bool,
    view: PropTypes.bool,
    activeExercise: PropTypes.string,
    menuPath: PropTypes.object,
    anonymous: PropTypes.bool
  };
  render() {
    return (
      <div className="uk-grid ">
        <div className="myheader uk-width-1-1">
          <div className="exercise ">
            <StudentExercise />
          </div>
        </div>
      </div>
    );
  }
}

const mapStateToProps = (state) => ({
  selected: state.getIn(['selectedExercises'], immutable.List([])).length > 0 ? 'selected_yes' : 'selected_no',
  admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
  author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
  view: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
  student: state.getIn(['login', 'groups'], immutable.List([])).includes('Student'),
  activeExercise: state.get('activeExercise'),
  menuPath: state.get('menuPath'),
  compactview: state.getIn(['login', 'compactview'], true),
  anonymous: state.getIn(['login', 'groups'], immutable.List([])).includes('AnonymousStudent'),
  lti_login: state.getIn(['login', 'lti_login'], true),
  course_name: state.getIn(['course', 'course_name']),
  username: state.getIn(['login', 'username'])
});

export default connect(mapStateToProps)(BaseApp);
