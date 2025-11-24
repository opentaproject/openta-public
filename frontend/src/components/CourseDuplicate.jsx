import React, { Component } from 'react';
import { connect } from 'react-redux';

import { enqueueTask, fetchCourses } from '../fetchers.js';
import { updatePendingStateIn } from '../actions.js';

class BaseCourseDuplicate extends Component {
  // {onCourseDuplicate, coursePk, taskId, status, progress, done,course_name}) =>
  constructor(props) {
    super(props);
    this.state = {
      newname: '',
      days: '0',
      deadline_date: null,
      solution: null,
      difficulty: null,
      required: null,
      student_assets: null,
      image: null,
      allow_pdf: null,
      bonus: null,
      published: null,
      feedback: null,
      locked: null,
      action: null,
      username: null,
    };
  }

  handleChange = (e) => {
    if (e.target.type == 'checkbox') {
      this.setState({ [e.target.name]: e.target.checked });
    } else {
      this.setState({ [e.target.name]: e.target.value });
    }
  };

  render = (onCourseDuplicate, coursePk, taskId, status, progress, done, subdomain,username) => {
    var newname = this.state.newname;
    var days = this.state.days;
    var course_name = this.props.course_name;
    var coursePk = this.props.coursePk;
    var taskId = this.props.taskId;
    var status = this.props.status;
    var progress = this.props.progress;
    var done = this.props.done;
    var courses = this.props.courses;
    var action = this.props.action;
    var existing_courses = courses.map((course) => course.getIn(['course_name']).toString()).toArray();
    var subdomain = this.props.subdomain;
    if (action == 'modify') {
      this.state.newname = course_name;
      this.state.action = 'modify';
    } else {
      this.state.action = 'duplicate';
    }
    if ( "super" !=  this.props.username  && action == 'duplicate' ){
    return( <div className="uk-flex uk-flex-column uk-flex-middle uk-margin-left uk-panel uk-panel-box"> Only the server website admin can duplicate a  course </div>)
	    
    }
    if (action == 'duplicate' && this.state.newname == '' ) {
      var reg = /(\d+)(?!.*\d)/;
      var cn = subdomain;
      var num_ar = cn.match(reg);
      var reg2 = /^course-/;
      cn = cn.replace(reg2, '');
      if (num_ar) {
        var num = (parseInt(num_ar[0]) + 1).toString();
        cn = cn.replace(reg, num);
      } else {
        cn = cn + '-1';
      }
      var newname = cn;
      this.state.newname = newname;
    }
    var checks = Object.keys(this.state);
    checks.splice(0, 2);

    var checkfields = checks.map((name) => {
      var checked = this.state.name;
      if (typeof this.state[name] == 'boolean') {
        var checked = this.state[name];
      } else {
        var checked = true;
      }

      var desc = String(name);
      return (
        <tr key={name}>
          <td>
            <input type="checkbox" name={name} checked={checked} onChange={this.handleChange} />
          </td>
          <td> {desc} </td>
        </tr>
      );
    });

    var modify = action == 'modify' ? true : false;
    var duplicate = action == 'duplicate' ? true : false;
    var newname_ok = !existing_courses.includes(this.state.newname);
    var enable_click = (newname_ok && duplicate) || modify;
    var warning1 = modify
      ? 'The present course will be modified. '
      : 'A new course with  the subdomain ' + this.state.newname + ' will be created.';
    var warning2 = modify
      ? 'Students will be kept'
      : 'The new course  will have the same exercises as ' +
        course_name +
        ' but an empty studentlist. The original course ' +
        subdomain +
        ' will be unaffected. ';
    var dupeormodify = modify ? 'Modify the course ' : 'Duplicate the course ';
    var textclass = enable_click ? 'uk-text  uk-text-warning' : 'uk-text-primary';
    var buttonclass = enable_click ? 'uk-button uk-button-danger' : 'uk-button uk-button-primary';
    var buttonmessage = modify
      ? 'Click here to modify the present course: This cannot be undone '
      : 'Create the new course';

    return (
      <div className="uk-panel uk-background-muted uk-width-medium-1-2">
        <div className="uk-flex uk-flex-column uk-flex-middle uk-margin-left uk-panel uk-panel-box">
          <div>
            <h3>
              {' '}
              {dupeormodify} {course_name}
            </h3>
            <br />
            {enable_click && (
              <div className={textclass}>
                {' '}
                {warning1} <br />
                {warning2}{' '}
              </div>
            )}
            <br />
            <table>
              <tbody>
                <tr>
                  <td> New subdomain: </td>
                  <td>
                    {duplicate && (
                      <input type="text" name="newname" onChange={this.handleChange} value={this.state.newname}></input>
                    )}
                    {duplicate && !newname_ok && <div className="uk-text uk-text-warning"> Course exists </div>}
                    {modify && <div> {this.state.newname} </div>}
                  </td>
                </tr>
                {modify && (
                  <tr>
                    <td> Days to shift : </td>
                    <td>
                      {' '}
                      <input type="text" name="days" value={days} onChange={this.handleChange}></input>{' '}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            <br />
            {modify && (
              <div>
                <div className={textclass}>
                  {' '}
                  Put a check by the exercise options in {this.state.newname} that should be kept
                </div>
                <br />
                <table>
                  <tbody>{checkfields}</tbody>
                </table>
              </div>
            )}
            <br />
            {enable_click && (
              <div onClick={() => this.props.onCourseDuplicate(coursePk, this.state)}>
                <button className={buttonclass} type="button">
                  {' '}
                  {buttonmessage}{' '}
                </button>{' '}
              </div>
            )}
          </div>
          <div className="uk-width-1-1 uk-margin-top">
            {progress >= 0 && done !== true && (
              <div className="uk-progress">
                <div className="uk-progress-bar" style={{ width: progress + '%' }}>
                  {progress}%
                </div>
              </div>
            )}
          </div>
          {status && <div className="uk-alert uk-alert-info">{status}</div>}
          {done && (
            <div>
              <i className="uk-icon uk-icon-check" />
            </div>
          )}
        </div>
      </div>
    );
  };
}
const mapDispatchToProps = (dispatch) => ({
  onCourseDuplicate: (coursePk, data) => {
    // ,days,checked1,checked2) => {
    var days = data.days;
    var newname = data.newname;
    var checked1 = data.checked1;
    var checked2 = data.checked2;
    var enqueueOptions = {
      completeAction: () => (dispatch) => dispatch(fetchCourses()),
      method: 'POST',
      data: data
    };
    dispatch(enqueueTask('/course/' + coursePk + '/duplicate/', enqueueOptions)).then((taskId) =>
      dispatch(updatePendingStateIn(['course', coursePk, 'duplicate', 'task'], taskId))
    );
  }
});

const mapStateToProps = (state) => {
  var pendingState = state.get('pendingState');
  var coursePk = state.get('activeCourse');
  var taskId = pendingState.getIn(['course', coursePk, 'duplicate', 'task']);
  return {
    taskId: taskId,
    coursePk: coursePk,
    progress: state.getIn(['tasks', taskId, 'progress']),
    subdomain: state.getIn(['login', 'subdomain']),
    done: state.getIn(['tasks', taskId, 'done']),
    status: state.getIn(['tasks', taskId, 'status']),
    course_name: state.getIn(['courses', coursePk, 'course_name']),
    courses: state.getIn(['courses']),
    username: state.getIn(['login', 'username']),
	  
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseCourseDuplicate);
