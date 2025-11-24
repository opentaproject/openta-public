import React from 'react';
import { connect } from 'react-redux';

import { SUBPATH } from '../settings';
import { enqueueTask } from '../fetchers';
import { updatePendingStateIn } from '../actions';

const BaseCourseExport = ({ onExport, coursePk, taskId, progress, done, status }) => {
  return (
    <div className="uk-flex uk-flex-wrap uk-margin-top">
      <div className="uk-flex uk-flex-column uk-flex-middle uk-margin-left uk-panel uk-panel-box">
        <div>Download a zip file containing the database, student results  and exercises of this course. Store the download in a safe location.  Unzip it in a directory and check the contents. </div>
        <div className={status}>
          <a className="uk-button CourseExport" onClick={() => onExport(coursePk)}>
            Export course
          </a>
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
        {done && (
          <div>
            <a href={SUBPATH + '/queuetask/' + taskId + '/resultfile'}>Download course zip file</a>
          </div>
        )}
        {status && <div className="uk-alert uk-alert-info">{status}</div>}
      </div>
    </div>
  );
};

const mapDispatchToProps = (dispatch) => ({
  onExport: (coursePk) => {
    dispatch(enqueueTask('/course/' + coursePk + '/export/')).then((taskId) =>
      dispatch(updatePendingStateIn(['course', coursePk, 'export', 'task'], taskId))
    );
  }
});

const mapStateToProps = (state) => {
  var pendingState = state.get('pendingState');
  var coursePk = state.get('activeCourse');
  var taskId = pendingState.getIn(['course', coursePk, 'export', 'task']);
  return {
    taskId: taskId,
    coursePk: coursePk,
    progress: state.getIn(['tasks', taskId, 'progress']),
    status: state.getIn(['tasks', taskId, 'status']),
    done: state.getIn(['tasks', taskId, 'done'])
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseCourseExport);
