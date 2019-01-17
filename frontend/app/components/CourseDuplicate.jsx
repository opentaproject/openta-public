import React from 'react';
import { connect } from 'react-redux';

import { enqueueTask, fetchCourses } from '../fetchers.js';
import { updatePendingStateIn, updatePendingState } from '../actions.js';

const BaseCourseDuplicate = ({onCourseDuplicate, coursePk, taskId, status, progress, done}) => {
  return <div className="uk-flex uk-flex-wrap uk-margin-top">
      <div className="uk-flex uk-flex-column uk-flex-middle uk-margin-left uk-panel uk-panel-box">
        <div>Create a copy of the current course on this server, the exercises will get new keys.</div>
        <div>
          <a className="uk-button" onClick={() => onCourseDuplicate(coursePk)}>
            Duplicate course
          </a>
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
    </div>;
}

const mapDispatchToProps = (dispatch) => ({
  onCourseDuplicate: (coursePk) => {
    var enqueueOptions = {
        completeAction: () => dispatch => dispatch(fetchCourses())
    }
    dispatch(enqueueTask("/course/" + coursePk + "/duplicate", enqueueOptions)).then(taskId =>
      dispatch(updatePendingStateIn(["course", coursePk, "duplicate", "task"], taskId))
    );
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
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseCourseDuplicate)
