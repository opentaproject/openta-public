import React from 'react';
import { connect } from 'react-redux';

import Badge from './Badge.jsx';
import SafeImg from './SafeImg.jsx';
import ExerciseHoverMenu from './ExerciseHoverMenu.jsx';
import T from './Translation.jsx';
import ButtonCapture from './ButtonCapture.jsx';
import ChatIcon from './ChatIcon.jsx'

import immutable from 'immutable';
import moment from 'moment';
import { SUBPATH } from '../settings.js';

var difficulties = {
  1: 'Easy',
  2: 'Medium',
  3: 'Hard',
  none: ''
};

function yesorno(feedback, correct, enforce = false, icon_true = 'uk-icon-check', icon_false = 'uk-icon-close') {
  var icon_danger = 'uk-text-danger ';
  if (icon_false.match(/clock/g)) {
    icon_danger = 'uk-text-warning ';
    icon_danger = ' ';
  }
  icon_true = 'uk-icon-check';
  icon_false = 'uk-icon-close';

  var uk_icon_check = enforce
    ? correct | (correct == null)
      ? 'uk-text-success ' + icon_true
      : icon_danger + icon_false
    : correct | (correct == null)
    ? 'uk-text-muted ' + icon_true
    : 'uk-text-muted ' + icon_false;
  var icon = feedback ? uk_icon_check : 'uk-icon-eye-slash';

  return icon;
}

const BaseExerciseItem = ({
  onExerciseClick,
  exercise,
  exerciseState,
  metaImmutable,
  folder,
  subdomain,
  statistics,
  activityRange,
  author,
  displaystyle,
  compact,
  organize,
  exercisename,
  view,
  admin,
  lang,
  sidecar_count,
}) => {
  var showStatistics = view || admin || author;
  showStatistics = showStatistics && !compact;
  var meta = metaImmutable.toJS();
  var deadlineClass = ' uk-badge-success ';
  var questionClass = ' uk-text-success ';
  var legend = '';
  var dolegend = false;
  if (meta.difficulty != null) {
  }

  if (meta.recommended) {
    deadlineClass = ' uk-badge-success ';
    questionClass = ' uk-text-success ';
    legend = '+';
    dolegend = true;
  }

  if (meta.bonus) {
    deadlineClass = ' uk-badge-warning ';
    questionClass = ' uk-text-warning ';
    legend = 'Bonus';
    dolegend = true;
  }

  if (meta.required) {
    deadlineClass = ' uk-badge-primary ';
    questionClass = ' uk-text-primary ';
    legend = 'Obligatory';
    dolegend = true;
  }

  if (meta.deadline_date) {
    dolegend = false;
  }
  var responseAwaits = 0;
  var thumbnail = meta.thumbnail
  if (showStatistics) {
    var percent_complete = exerciseState.getIn([exercise, 'percent_complete'], 0);
    var percent_correct = exerciseState.getIn([exercise, 'percent_correct'], 0);
    var percent_tried = exerciseState.getIn([exercise, 'percent_tried'], 0);
    var maxActivity = statistics.getIn(['aggregates', 'max_' + activityRange], 0);
    var activity = 0;
    if (maxActivity > 0) {
      activity = (100 * exerciseState.getIn([exercise, 'activity', activityRange])) / maxActivity;
    }
    if (percent_complete === null) {
      percent_complete = 0;
    }
    if (percent_correct === null) {
      percent_correct = 0;
    }
    if (percent_tried === null) {
      percent_tried = 0;
    }
    var responseAwaits = Number(exerciseState.getIn([exercise, 'response_awaits'], 0));
  }
  var imageUploaded = exerciseState.getIn([exercise, 'image_answers'], immutable.List([])).size > 0;
  var image_exists = imageUploaded;
  var nameDict = folder.getIn(['exercises', exercise, 'translated_name']);
  var showCheck = exerciseState.getIn([exercise, 'show_check'], false);
  var showResponseAwaits = responseAwaits > 0;
  var all_complete = exerciseState.getIn([exercise, 'all_complete'], false);
  var correct = exerciseState.getIn([exercise, 'correct'], null);
  var complete_by_deadline = exerciseState.getIn([exercise, 'complete_by_deadline'], false);
  var audit_published = exerciseState.getIn([exercise, 'audit_published'], false);
  var audit_revision_needed = exerciseState.getIn([exercise, 'response_awaits'], false);
  var image_by_deadline = exerciseState.getIn([exercise, 'image_by_deadline'], false);
  var correct_by_deadline = exerciseState.getIn([exercise, 'correct_by_deadline'], false);
  var questionlist_is_empty =  exerciseState.getIn([exercise, 'questionlist_is_empty'], true );
  var questions_exist = ! questionlist_is_empty
  var show_check = exerciseState.getIn([exercise, 'show_check'], true);
  var ignore_no_feedback = exerciseState.getIn([exercise, 'ignore_no_feedback']);
  var feedback = meta.feedback | ignore_no_feedback;
  var feedback_safe = true;
  if (meta.published) {
    var box_color = 'exercise-incomplete';
    if (all_complete) {
      box_color = 'exercise-all_complete';
    }
    if (complete_by_deadline) {
      box_color = 'exercise-complete_by_deadline';
    }
    if (!feedback) {
      box_color = 'exercise-ungraded';
    } 
  } else {
    var box_color = 'exercise-unpublished';
  }
  if ( questionlist_is_empty ){
	  var box_color = ''
  }

  var check_badge_color = correct_by_deadline ? 'uk-badge-success' : correct ? 'uk-badge-warning' : 'uk-badge-danger';
  var uk_icon_check = correct | (correct == null) ? 'uk-icon-check' : 'uk-icon-close';
  var imageUploadClass = imageUploaded
    ? image_by_deadline
      ? 'uk-badge-success'
      : 'uk-badge-warn'
    : 'uk-badge-dang';
  var ringClass = 'uk-icon uk-text-primary uk-icon-tiny uk-icon-life-ring';
  var aiClass = 'uk-icon uk-text-primary uk-icon-tiny uk-icon-life-ring';
  var bb = '</td><td>';
  var cbd = 'X';
  var image_date = exerciseState.getIn([exercise, 'image_date'], null);
  var answer_date = exerciseState.getIn([exercise, 'answer_date'], null);
  var image_deltat = exerciseState.getIn([exercise, 'image_deltat'], null);
  var all_complete = exerciseState.getIn([exercise, 'all_complete'], false);
  var audit_published = exerciseState.getIn([exercise, 'audit_published'], false);
  var audit_passed = !exerciseState.getIn([exercise, 'response_awaits'], true);
  var meta  = metaImmutable.toJS() ; // exerciseState.getIn([exercise], null).toJS()  
  var answer_deltat = exerciseState.getIn([exercise, 'answer_deltat'], null);
  if ( audit_published ){
  		var points = exerciseState.getIn([exercise, 'points'], '0' );
	} else { if  ( !( meta.required | meta.bonus ) ) {
			var points = ''
		} else { 
			var points =  all_complete ? 1 : 0 
		}
	}
  var default_name = folder.getIn(["exercises", exercise, "name"])
  var exercisename =  nameDict.getIn([lang], default_name) 
  var qe = questions_exist ? "yes" : "no"
  //console.log("QE = ", qe , questions_exist, exercisename, nameDict.toJS()  )
  if (displaystyle == 'detail') {
    var name = exerciseState.getIn([exercise, 'name'], 'NONAME');
    var enforce_deadline = meta.deadline_date ? true : false;
    var no_deadline = ! enforce_deadline
    var enforce_image = meta.image ? true : false;
    var enforce_answer_questions = questions_exist && feedback;
    if (questions_exist) {
      var answer_deltat = enforce_deadline ? exerciseState.getIn([exercise, 'answer_deltat'], null) : '';
    } else {
      var answer_deltat = '';
    }

    var image_deltat = !enforce_deadline
      ? 'no deadline '
      : image_exists
      ? exerciseState.getIn([exercise, 'image_deltat'], null)
      : 'image missing';
    if (!enforce_image) {
      image_deltat = 'no image required';
    }
    var date_complete = exerciseState.getIn([exercise, 'date_complete'], null)
    var duedate = (meta.deadline_date ? meta.deadline_date + ' at ' + meta.deadline_time : 'no duedate').replace(
      '23:59:59',
      'midnight'
    );
    /*if ( meta.deadline_date && '23:59:59' == meta.deadline_time ){
      var duedate = meta.deadline_date + ' midnight'
    } else {
       var duedate = meta.deadline_date  ? ( meta.deadline_date  + ' at ' + meta.deadline_time) : "no duedate"
      }

    var due_datetime = exerciseState.getIn([exercise, "due_datetime"], "no deadline")
    due_datetime = due_datetime.replace('23:59:59',' midnight')
    */
    var show_data = date_complete == null ? false : true;
    var auditor =
      exerciseState.getIn([exercise, 'audit', 'auditor_data', 'first_name'], '') +
      ' ' +
      exerciseState.getIn([exercise, 'audit', 'auditor_data', 'last_name'], '');
    var audit_published = exerciseState.getIn([exercise,'audit','published'],null );
    var audit_message = audit_published ? exerciseState.getIn([exercise, 'audit', 'message'], 'no audits published') + ' ' + auditor  :  '' 
    audit_message = audit_message.trim();
    show_data = true;
    console.log("DATE_COMPLETE = ", date_complete )
    if ( date_complete == null ){ date_complete = '' } 
    if (!show_data) {
      return (
        <div className="uk-margin-remove uk-padding-remove" key={exercise + 'exercise-item'}>
          <table className="exercise_item uk-width-1-1">
            <tbody>
              <tr>
                <td className={'uk-padding-remove uk-margin-remove column_name 30'}>
                  <a onClick={(ev) => onExerciseClick(exercise, subdomain)}>
                    <div className={'uk-text ' + questionClass}> {exerisename} </div>
                  </a>{' '}
                </td>
                <td className={'column_date uk-hidden-small 15'}>{duedate}</td>
                <td className="no_data uk-hidden-small "> no data </td>
              </tr>
            </tbody>
          </table>
        </div>
      );
    } else {
      return (
        <div id={exercise}>
          <table className="exercise_item uk-width-1-1">
            <tbody>
              <tr>
                <td className={'uk-padding-remove column_name 30'}>
                  <a onClick={(ev) => onExerciseClick(exercise, subdomain)}>
                    <div className={'uk-text ' + questionClass}>
                      <i className={'uk-inline uk-icon uk-icon-circle padright'} />
                      {exercisename} 
                    </div>
                  </a>{' '}
                </td>

                <td className={'uk-hidden-small column_date 15'}>{duedate}</td>

                <td className={'column_check_main 5 '}>
	      {  questions_exist && (
                  <i className={'uk-icon ' + yesorno(feedback, all_complete, true)} data-uk-tooltip title="Task completed?" /> )}
	      { ! no_deadline && (
                  <i className={ 'uk-icon ' + yesorno(feedback, no_deadline || complete_by_deadline  , enforce_deadline, 'uk-icon-check', 'uk-icon-clock-o') } data-uk-tooltip title="On time?" />
	      ) }
                </td>

                <td data-uk-tooltip="delay:500; pos: right" title={audit_message} className={'column_date_main 15'}> {date_complete} </td>

                <td className={'uk-hidden-small column_check 5'}>
	      { questions_exist && (
                  <i className={'uk-icon ' + yesorno(feedback, correct, enforce_answer_questions)} data-uk-tooltip title="Correct autograded answers?" />
	      ) }
	      { questions_exist && enforce_deadline && (
                  <i className={ 'uk-icon ' + yesorno( feedback, no_deadline || correct_by_deadline , enforce_answer_questions && enforce_deadline, 'uk-icon-check', 'uk-icon-clock-o') } data-uk-tooltip title="Answers on time?" />
	      ) }
	   { !  questions_exist && (
                  <i className={ "uk-icon uk-icon-check" } data-uk-tooltip title="No questions need answer" />
	      ) }
                </td>
                <td className={'uk-hidden-small column_date 15'}> {answer_deltat} </td>
                <td className={'uk-hidden-small column_check 5 '}>
                  <i className={'uk-icon ' + yesorno(feedback_safe, image_exists, enforce_image)} data-uk-tooltip title="Image exists?" />
                  <i
                    className={
                      'uk-icon ' +
                      yesorno(
                        feedback_safe,
                        image_by_deadline,
                        enforce_deadline && enforce_image,
                        'uk-icon-check',
                        'uk-icon-clock-o'
                      )
                    } data-uk-tooltip title="Image on time?"
                  />
                </td>
                <td className={'uk-hidden-small column_date 15'}>{image_deltat}</td>
                <td
                  className={'uk-hidden-small column_check 5'}
                  data-uk-tooltip="delay:500; pos: left"
                  title={audit_message}
                >
                  {' '}
                  <span data-uk-tooltip title="Points" >  {points}  </span>
	      { audit_published && (
                  <i className={'uk-icon ' + yesorno(feedback_safe , (  audit_passed ), audit_published)} data-uk-tooltip title="Final?" /> ) } 
{ ! audit_published && (
                  <i className={'uk-icon ' + yesorno(feedback_safe , (  audit_passed ), audit_published)} data-uk-tooltip title="Not audited" /> ) }

	      {' '} 
	      </td>
              </tr>
            </tbody>
          </table>
        </div>
      );
    }
  } else {

    var style = { minWidth: '80px', maxWidth: '100px', height: '80px' }
    if ( thumbnail  ){
    var style = { minWidth: '80px', maxWidth: '100px', 
 		background : "url(" + '/exercise/' + exercise + '/asset/' + thumbnail  + ") no-repeat",
		width: '100%',
		height: '80px', }
      }

    try {
    var c2 = sidecar_count.get('unread').includes( exercise )
    var c1 = sidecar_count.get('exercises_with_posts').includes( exercise )
    var sc = c2 ?  2 : ( c1 ? 1 : 0  )
    } catch { var sc = 0 } 
    var sidecar_class = ['','uk-icon uk-icon-circle-o','uk-text-danger uk-icon uk-icon-circle' ]



    return (
      <div
        key={exercise + 'abbba'}
        className="uk-position-relative"
        data-uk-dropdown="{hoverDelayIdle: 0, delay: 300, pos: 'top-center'}"
      >
        {/*
      <li key={folderName}>

              <a onClick={() => {
                  UIkit.modal("#move-modal-ABC" + folder_key ).hide();
                  fcn(folderPath, content.get('path').join('/'), coursePk);
                }} className="uk-modal-close">
                    {folderNameRender}
                </a>

                <ul key={folder_key + 'folder_key'} className="uk-list">
                    { subfolders }
                </ul>
            </li>
      */}

        <ButtonCapture organize={organize} exerciseKey={exercise}>
          <a
            id={'course-exercise-item-button'}
            className={'uk-thumbnail exercise-a ' + box_color}
            onClick={(ev) => onExerciseClick(exercise, subdomain)}
          >
            <div className="exercise-thumb-wrap" style={style}>
              <div className="exercise-thumb-badge">
                {meta.difficulty && (
                  <Badge className="uk-badge-notification">
                    <T>{meta.difficulty}</T>
                  </Badge>
                )}
                {meta.deadline_date && (
                  <Badge className={'uk-badge-notification ' + deadlineClass} title={legend}>
                    {moment(meta.deadline_date).format('D MMM')}
                  </Badge>
                )}
                {dolegend && (
                  <Badge className={'uk-badge-notification ' + deadlineClass} title={'Recommended'}>
                    <T>{legend}</T>
                  </Badge>
                )}

                {meta.image && (
                  <span className={'uk-badge uk-badge-notification ' + imageUploadClass}>
                    <i className="uk-icon uk-icon-camera" />
                  </span>
                )}
		{meta.allow_ai && ( <ChatIcon />) }
                {meta.solution && <i className={ringClass} />}
                {showCheck && !meta.feedback && (
                  <span className="uk-badge uk-badge-notification">
                    <i className={'uk-icon ' + uk_icon_check} />
                  </span>
                )}
                {showCheck && meta.feedback && (
                  <span className={'uk-badge uk-badge-notification ' + check_badge_color}>
                    <i className={'uk-icon ' + uk_icon_check} />
                  </span>
                )}
                {showResponseAwaits && (
                  <i className="uk-text-danger uk-margin-small-left uk-icon uk-icon uk-icon-envelope" />
                )}
                {exerciseState.getIn([exercise, 'modified']) && (
                  <Badge className={'uk-badge-notification uk-badge-danger'}>
                    <i className="uk-icon uk-icon-save" />
                  </Badge>
                )}
                {audit_published && (
                  <Badge type={audit_revision_needed ? 'error' : 'success'} className={'uk-badge-notification'}>
                    {' '}
                    Audited
                  </Badge>
                )}
                {!meta.published && (
                  <Badge type="error" title="Unpublished" className={'uk-badge-notification uk-float-right'}>
                    <T>Unpublished</T>
                  </Badge>
                )}
              </div>
            </div>
            <div className={'uk-thumbnail-caption exercise-thumb-nav-caption '}>
	    <h4 className="uk-margin-remove">{exercisename} &nbsp; <i className={  sidecar_class[ sc ] }></i>   </h4>
            </div>
            {showStatistics && !meta.deadline_date && (
              <div
                className="uk-progress uk-margin-remove uk-progress-small uk-progress-warning"
                title="blue: correct, orange: tried"
              >
                <div
                  className="uk-progress-bar"
                  style={{ width: percent_correct * 100 + '%', backgroundColor: '#00a8e6' }}
                />
                <div className="uk-progress-bar" style={{ width: (percent_tried - percent_correct) * 100 + '%' }} />
              </div>
            )}
            {showStatistics && meta.deadline_date && (
              <div
                className="uk-progress uk-margin-remove uk-progress-small uk-progress-success"
                title="green: complete, blue: correct, orange: tried"
              >
                <div className="uk-progress-bar" style={{ width: percent_complete * 100 + '%' }} />
                <div
                  className="uk-progress-bar"
                  style={{ width: (percent_correct - percent_complete) * 100 + '%', backgroundColor: '#00a8e6' }}
                />
                <div
                  className="uk-progress-bar"
                  style={{ width: (percent_tried - percent_correct) * 100 + '%', backgroundColor: '#faa732' }}
                />
              </div>
            )}
            {activity >= 0 && (
              <div className="uk-progress uk-margin-remove uk-progress-small uk-progress-danger" title="Tries/Question">
                <div
                  className="uk-progress-bar uk-text-small"
                  style={{ width: activity + '%', backgroundColor: '#de96e2' }}
                >
                  {activity >= 10 && (
                    <span className="uk-text-small">{exerciseState.getIn([exercise, 'activity', activityRange])}</span>
                  )}
                  {activity < 10 && activity > 0 && (
                    <span style={{ position: 'relative', left: '200%' }} className="uk-text-danger uk-text-small">
                      {exerciseState.getIn([exercise, 'activity', activityRange])}
                    </span>
                  )}
                  {activity == 0 && <span className="uk-text-primary uk-text-small">0</span>}
                </div>
              </div>
            )}
          </a>
        </ButtonCapture>
        {author && (
          <div className="uk-dropdown uk-dropdown-small uk-margin-remove" style={{ minWidth: 10 }}>
            <ExerciseHoverMenu exercisename={exercisename} exerciseKey={exercise} />
          </div>
        )}
        {/* organize && (
        <div>
        <span id="#my-id" data-uk-modal>x</span>
        <button className="uk-button" data-uk-modal="{target:'#my-id'}">Action</button>
        <div id="my-id" className="uk-modal">
          <div className="uk-dropdown uk-dropdown-small uk-margin-remove" style={{ minWidth: 10 }}>
            <div className="uk-modal-dialog">

        <ul>
        <li> <a className="uk-modal-close uk-close"> Hit close1 </a> </li>
        <li> <a className="uk-modal-close uk-close"> Hit close2 </a> </li>
        <li> <ExerciseHoverMenu exerciseKey={exercise} /> </li>
        </ul> 
      </div>

        </div>
        </div>
        </div>
        ) */}
      </div>
    );
  }
};

const mapStateToProps = (state) => ({
  exerciseState: state.get('exerciseState'),
  displaystyle: state.get('displaystyle'),
  statistics: state.get('statistics', immutable.Map({})),
  activityRange: state.get('activityRange', '1h'),
  student: state.getIn(['login', 'groups'], immutable.List([])).includes('Student'),
  author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
  view: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
  admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
  subdomain: state.getIn(['login', 'subdomain']),
  selectedExercises: state.getIn(['selectedExercises'], []),
  lang: state.getIn(['lang']),
  sidecar_count :  state.getIn(['login', 'sidecar_count'], immutable.List([])),

});

export default connect(mapStateToProps, null)(BaseExerciseItem);
