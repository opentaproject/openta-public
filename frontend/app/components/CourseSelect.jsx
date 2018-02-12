import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import T from './Translation.jsx';

import {
  setActiveCourse
} from '../actions.js';

import {
  fetchExercises,
  fetchExerciseTree
} from '../fetchers.js';

const BaseCourseSelect = ({courses, activeCourse, onCourseChange}) => {
  if(courses == null || (courses.size == 1 && courses.first() == ''))
    return (<span/>);
  var courseChoices = courses.map(course =>
    <li className="uk-text-center" key={course.get('pk')}>
      <a className="uk-dropdown-close" style={{padding:"0px 5px"}} onClick={() => onCourseChange(course.get('pk'))}>
        <span className={course.pk == activeCourse ? 'uk-text-bold' : ''}>{course.get('course_name')}</span>
      </a>
    </li>).toList();
  return <div className="uk-button-dropdown" data-uk-dropdown="{mode:'click'}">
    <button className="uk-button uk-button-mini uk-button-success">
      {courses.getIn([activeCourse, 'course_name'])}
      <i className="uk-margin-small-left uk-icon-caret-down"></i>
    </button>
    <div className="uk-dropdown uk-dropdown-small uk-dropdown-bottom" style={{minWidth:'0'}}>
      <ul className="uk-nav uk-nav-dropdown" style={{padding:'0'}}>
        <li key="header" className="uk-nav-header"><T>Course</T></li>
        {courseChoices}
      </ul>
    </div>
  </div>;
}

const mapDispatchToProps = dispatch => {
    return {
        onCourseChange: (course) => {
            dispatch(setActiveCourse(course));
            dispatch(fetchExercises(course));
            dispatch(fetchExerciseTree(course));
        }
    }
}

const mapStateToProps = (state) => {
    return {
      courses: state.getIn(['courses'], immutable.Map({})),
      activeCourse: state.get('activeCourse'),
    };
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseCourseSelect);
