import React , {Component} from 'react';
import { connect } from 'react-redux';

import { enqueueTask, fetchCourses } from '../fetchers.js';
import { updatePendingStateIn, updatePendingState } from '../actions.js';
import { renderText } from './questiontypes/render_text.js';




class BaseCourseDuplicate extends Component  {
  // {onCourseDuplicate, coursePk, taskId, status, progress, done,course_name}) => 
  constructor() {
    super();
    this.state = {
      newname: '',
      days: '0',
    deadline_date : false,
    solution : false,
    difficulty : false,
    required : false,
    student_assets : false,
    image : false,
    allow_pdf : false,
    bonus : false,
    published : false,
    feedback : false,
    }

  }

  handleChange = (e) => {
    if ( e.target.type == 'checkbox'  ){
      this.setState({ [e.target.name]: e.target.checked })
    } else {
      this.setState({ [e.target.name]: e.target.value }  )
    }
  }


  render = ( onCourseDuplicate, coursePk, taskId, status, progress, done) =>  {
  var newname = this.state.newname
  var days = this.state.days
  var course_name = this.props.course_name
  var coursePk = this.props.coursePk
  var taskId = this.props.taskId
  var status = this.props.status
  var progress  = this.props.progress
  var done = this.props.done
  if( newname ==  '' ){
    this.state.newname = course_name
  }
  var checks =  Object.keys(this.state)
  checks.splice(0,2)

 var checkfields = checks.map((name) => {
      var checked= this.state.name
      var desc = String( name)
      return( 
        <tr key={name}>
          <td>
        <input  type="checkbox" name={name} checked={checked}  onChange={this.handleChange} /> 
        </td>
<td> {desc} </td>
        </tr>
      )
    }
 )

 var warning1 = ( this.state.newname == course_name ) ? "The present course will be modified. " : "A new course with name " + this.state.newname + " will be created."
 var warning2 = ( this.state.newname == course_name ) ? "Students will be kept" :  "The new course  will have the same exercises as " + course_name + 
        " but an empty studentlist. The original course " +  course_name + "will be unaffected. "
 var dupeormodify = (this.state.newname == course_name ) ? "Modify the course " : "Duplicate the course "
 var textclass = (this.state.newname == course_name ) ? "uk-text  uk-text-warning" : "uk-text-primary"
 var buttonclass = (this.state.newname == course_name ) ? "uk-button uk-button-danger" : "uk-button uk-button-primary"
 var buttonmessage = (this.state.newname == course_name ) ? "Click here to modify the present course: This cannot be undone " : "Create the new course"

  

  return   ( 
    <div className="uk-panel uk-background-muted uk-width-medium-1-2">
      <div className="uk-flex uk-flex-column uk-flex-middle uk-margin-left uk-panel uk-panel-box">
        <div>
          <h3>  {dupeormodify} {course_name}</h3>
          <br/>
<div className={textclass}> (*) {warning1} <br/>{warning2} </div>
        <br/>
          <table>
            <tbody>
              <tr><td> Course name: </td><td>  <input type="text" name="newname"
                onChange={this.handleChange}
                value={this.state.newname}
              ></input>  (*)  </td></tr>
              <tr><td> Days to shift : </td><td>  <input type="text" name="days"
                value={days}
                onChange={this.handleChange}
              ></input>  </td></tr>
            </tbody>
          </table>
          <br/>
          <div className={textclass} > Put a check by the options in {this.state.newname} that should be reset to default</div>
          <br/>
          <table>
            <tbody>
             {checkfields}
             </tbody>
            </table>
          <br/>
          <div onClick={() => this.props.onCourseDuplicate(coursePk, this.state ) }> 
            <button className={buttonclass}  type="button"> {buttonmessage} </button> </div>
        </div>
        <div className="uk-width-1-1 uk-margin-top">
          {progress >= 0 && done !== true && <div className="uk-progress">
            <div className="uk-progress-bar" style={{ width: progress + "%" }}>
              {progress}%
                </div>
          </div>}
        </div>
        {status && <div className="uk-alert uk-alert-info">{status}</div>}
        {done && <div>
          <i className="uk-icon uk-icon-check" />
        </div>}
      </div>
    </div >
    )
    }

}
const mapDispatchToProps = (dispatch) => ({
  onCourseDuplicate: (coursePk,  data ) => { // ,days,checked1,checked2) => {
    var days= data.days
    var newname = data.newname;
    var checked1 = data.checked1;
    var checked2 = data.checked2;
    var enqueueOptions = {
        completeAction: () => dispatch => dispatch(fetchCourses()),
        method: 'POST',
        data: data,
    }
    dispatch(enqueueTask("/course/" + coursePk + "/duplicate/", enqueueOptions))
      .then(taskId => dispatch(updatePendingStateIn(["course", coursePk, "duplicate", "task"], taskId)));
  }
})

const mapStateToProps = (state) => {
  var pendingState = state.get('pendingState');
  var coursePk = state.get('activeCourse');
  var taskId = pendingState.getIn(["course", coursePk, "duplicate", "task"]);
  return {
    taskId: taskId,
    coursePk: coursePk,
    progress: state.getIn(['tasks', taskId, 'progress']),
    done: state.getIn(['tasks', taskId, 'done']),
    status: state.getIn(['tasks', taskId, 'status']),
    course_name: state.getIn(['courses',coursePk,'course_name']),
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseCourseDuplicate)
