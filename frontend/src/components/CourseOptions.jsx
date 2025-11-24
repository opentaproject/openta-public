import React, { Component } from 'react';
import { connect } from 'react-redux';
import { SUBPATH } from '../settings.js';
import { getcookie } from '../cookies.js';

import { fetchCourse, fetchCourses } from '../fetchers.js';

class BaseCourseOptions extends Component {
  render() {
    var activeCourse = this.props.activeCourse;
    return (
      <div className="uk-panel uk-panel-box uk-panel-box-secondary uk-margin-top">
        <iframe
          key={activeCourse}
          scrolling="yes"
          className="options"
          src={SUBPATH + '/course/' + activeCourse + '/updateoptions/'}
          onLoad={(event) => this.handleIframeLoad(event, this.props.onCourseUpdate(activeCourse))}
        />
      </div>
    );
  }

  handleIframeLoad = (event, onOptionsSubmit) => {
    var submitted_cookie = getcookie('submitted', event.target.contentDocument);
    if (submitted_cookie.length > 0 && submitted_cookie[0] === 'true') {
      onOptionsSubmit();
    }
  };
}

const mapDispatchToProps = (dispatch) => {
  return {
    onCourseUpdate: (course) => {
      dispatch(fetchCourses());
      dispatch(fetchCourse(course));
    }
  };
};

const mapStateToProps = (state) => {
  return {
    activeCourse: state.get('activeCourse')
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseCourseOptions);
