import React, { Component } from 'react';
import { connect } from 'react-redux'

import Spinner from "./Spinner.jsx";
import Badge from "./Badge.jsx";
import SafeImg from "./SafeImg.jsx";
import AddExercise from "./AddExercise.jsx";
import ExerciseHoverMenu from "./ExerciseHoverMenu.jsx";
import FolderHoverMenu from "./FolderHoverMenu.jsx";
import T from "./Translation.jsx";
import t from "../translations.js";

import immutable from "immutable";
import moment from "moment";
import { SUBPATH } from "../settings.js";
import { updateExercises, updateExerciseTreeUI } from "../actions.js";
import { navigateMenuArray } from "../menu.js";

var difficulties = {
  "1": "Easy",
  "2": "Medium",
  "3": "Hard",
  none: ""
};

import {
  fetchExercise,
  fetchExerciseRemoteState,
  fetchExercises,
  fetchSameFolder,
  fetchAddExercise,
  updatePendingStateIn
} from "../fetchers.js";


function yesorno(feedback,correct,enforce=false,icon_true='uk-icon-check',icon_false ='uk-icon-close') {

var icon_danger = 'uk-text-danger '
if( icon_false.match(/clock/g) ){
    icon_danger = 'uk-text-warning '
    icon_danger = ' '
    }
icon_true = 'uk-icon-check'
icon_false = 'uk-icon-close'

var uk_icon_check = enforce ? ( ( correct | ( correct == null ) )  ? 'uk-text-success ' + icon_true  : icon_danger  + icon_false ) :
            ( correct | ( correct == null ) )  ? 'uk-text-muted ' + icon_true : 'uk-text-muted ' + icon_false
var icon = feedback ? uk_icon_check :  'uk-icon-eye-slash'
            
return (icon)

}

const BaseExerciseItem = ({ onExerciseClick, exercise, exerciseState, metaImmutable,
  folder, foldername, showStatistics, statistics, activityRange, author , displaystyle, compact, 
}) => {


  showStatistics = showStatistics && ( ! compact )
  var meta = metaImmutable.toJS();
  var deadlineClass = " uk-badge-success ";
  var questionClass = " uk-text-success "
  var legend = ''
  var dolegend = false
  if ( meta.difficulty != null ){
  }

  if ( meta.recommended) {
    deadlineClass = " uk-badge-success ";
    questionClass = " uk-text-success "
    legend = '+';
    dolegend = true
  }

  if (meta.bonus) {
    deadlineClass = " uk-badge-warning ";
    questionClass = " uk-text-warning "
    legend = "Bonus";
    dolegend = true
  }
  
  if (meta.required) {
    deadlineClass = " uk-badge-primary ";
    questionClass = " uk-text-primary "
    legend = "Obligatory";
    dolegend = true
  }



  if ( meta.deadline_date ) {
    dolegend = false
    }
  var responseAwaits = 0
  if (showStatistics  ) {
    var percent_complete = exerciseState.getIn([exercise, "percent_complete"], 0);
    var percent_correct = exerciseState.getIn([exercise, "percent_correct"], 0);
    var percent_tried = exerciseState.getIn([exercise, "percent_tried"], 0);
    var maxActivity = statistics.getIn(["aggregates", "max_" + activityRange], 0);
    var activity = 0;
    if (maxActivity > 0) activity = (100 * exerciseState.getIn([exercise, "activity", activityRange])) / maxActivity;
    if (percent_complete === null) percent_complete = 0;
    if (percent_correct === null) percent_correct = 0;
    if (percent_tried === null) percent_tried = 0;
    var responseAwaits = Number(exerciseState.getIn([exercise, "response_awaits"], 0));
  }
  var imageUploaded = exerciseState.getIn([exercise, "image_answers"], immutable.List([])).size > 0;
  var image_exists = imageUploaded 
  var nameDict = folder.getIn(["exercises", exercise, "translated_name"]);
  var showCheck = exerciseState.getIn([exercise, "show_check"], false);
  var showResponseAwaits = responseAwaits > 0;
  var all_complete =  exerciseState.getIn([exercise, "all_complete"], false);
  var correct =  exerciseState.getIn([exercise, "correct"], null);
  var complete_by_deadline  =  exerciseState.getIn([exercise, "complete_by_deadline"], false);
  var audit_published =  exerciseState.getIn([exercise, "audit_published"], false);
  var audit_revision_needed =  exerciseState.getIn([exercise, "response_awaits"], false);
  var image_by_deadline  =  exerciseState.getIn([exercise, "image_by_deadline"], false);
  var correct_by_deadline  =  exerciseState.getIn([exercise, "correct_by_deadline"], false);
  var questions_exist =  exerciseState.getIn([exercise, "questions_exist"], null);
  // false below disables checkmarks for course for ffm770
  var show_check =  exerciseState.getIn([exercise, "show_check"], true);
  var ignore_no_feedback =  exerciseState.getIn([exercise, "ignore_no_feedback"])
  var feedback = meta.feedback  | ignore_no_feedback
  var feedback_safe = true
  if ( meta.published  ){
    var box_color = 'exercise-incomplete'
    if ( all_complete  ) {
        box_color = 'exercise-all_complete'
        }
    if ( complete_by_deadline) {
        box_color = 'exercise-complete_by_deadline'
        }
    if ( ! feedback ){
        box_color = 'exercise-ungraded'
       }
    } else {
        var box_color = 'exercise-unpublished'
    }
  var check_badge_color = correct_by_deadline ?  'uk-badge-success'  : 
      ( correct ? 'uk-badge-warning' : 'uk-badge-danger' )
  var uk_icon_check = ( correct | ( correct == null ) )  ? 'uk-icon-check' : 'uk-icon-close'
  var imageUploadClass = imageUploaded ? ( image_by_deadline ? "uk-badge-success" : "uk-badge-warning" ) : "uk-badge-danger";
  var ringClass = "uk-icon uk-text-primary uk-icon-tiny uk-icon-life-ring";
  var bb = "</td><td>"
  var cbd = "X"
  var image_date = exerciseState.getIn([exercise, "image_date"], null)
  var answer_date = exerciseState.getIn([exercise, "answer_date"], null)
  var image_deltat= exerciseState.getIn([exercise, "image_deltat"], null)
  var all_complete = exerciseState.getIn([exercise, "all_complete"], false)
  var audit_published = exerciseState.getIn([exercise, "audit_published"], false)
  var audit_passed = ! exerciseState.getIn([exercise, "response_awaits"], true)
  var answer_deltat = exerciseState.getIn([exercise, "answer_deltat"], null)
  var points = exerciseState.getIn([exercise, "points"], null)
  var exercisename = folder.getIn(["exercises", exercise, "name"])
  if (displaystyle == "detail"){
    var name=exerciseState.getIn([exercise,"name"],'NONAME')
    var enforce_deadline = meta.deadline_date ? true : false
    var enforce_image = meta.image? true : false
    var enforce_answer_questions = questions_exist && feedback
    if( questions_exist ){
        var answer_deltat =   ( enforce_deadline ? exerciseState.getIn([exercise, "answer_deltat"], null) : "no deadline") 
        } else {
        var answer_deltat = " unanswered"
        }
        
    var image_deltat=   ! enforce_deadline ?  "no deadline " : (
             image_exists ? exerciseState.getIn([exercise, "image_deltat"], null) : "image missing" )
    if ( ! enforce_image  ){
            image_deltat = "no image required"
        }
    var date_complete =  exerciseState.getIn([exercise, "date_complete"], null)
    var duedate = ( meta.deadline_date  ? ( meta.deadline_date  + ' at ' + meta.deadline_time) : "no duedate" ).replace("23:59:59", "midnight")
    /*if ( meta.deadline_date && '23:59:59' == meta.deadline_time ){
      var duedate = meta.deadline_date + ' midnight'
    } else {
       var duedate = meta.deadline_date  ? ( meta.deadline_date  + ' at ' + meta.deadline_time) : "no duedate"
      }

    var due_datetime = exerciseState.getIn([exercise, "due_datetime"], "no deadline")
    due_datetime = due_datetime.replace('23:59:59',' midnight')
    */
    var show_data = ( date_complete == null ) ? false : true 
    var auditor =  exerciseState.getIn([exercise,'audit','auditor_data','first_name'],'') + ' ' + 
            exerciseState.getIn([exercise,'audit','auditor_data','last_name'],'') 

    var audit_message = exerciseState.getIn([exercise,'audit','message'],'no audits published')  + " " + auditor
    audit_message = audit_message.trim()
    show_data = true
    if ( ! show_data ){
      return(
    <div className="uk-margin-remove uk-padding-remove" id={exercise}>
    <table className="exercise_item uk-width-1-1">
    <tbody>
        <tr>
        
        <td className={"uk-padding-remove uk-margin-remove column_name 30"}>
        <a onClick={ev => onExerciseClick(exercise, foldername)} >
            <div className={"uk-text " + questionClass }> <T dict={nameDict}>{folder.getIn(["exercises", exercise, "name"])}</T> </div> 
        </a> </td>
      <td className={"column_date uk-hidden-small 15"}>{duedate}</td>
        <td className="no_data uk-hidden-small "> no data </td>
        </tr>
     </tbody>
      </table></div>)
    } else {

    return(
    <div id={exercise}>
    <table className="exercise_item uk-width-1-1">
    <tbody>
        <tr>
        <td className={"uk-padding-remove column_name 30"}>
        <a onClick={ev => onExerciseClick(exercise, foldername)} >
            <div className={"uk-text " + questionClass }> 
            <i className={'uk-inline uk-icon uk-icon-circle padright' } />
            <T dict={nameDict}>{folder.getIn(["exercises", exercise, "name"])}</T> 
                </div> 
        </a> </td>

        <td className={"uk-hidden-small column_date 15"}>
            {duedate}
        </td>


        <td className={"column_check_main 5 "}><i className={"uk-icon "  + yesorno(feedback,all_complete,true) } />
        <i className={"uk-icon "  + yesorno(feedback,complete_by_deadline,enforce_deadline , 'uk-icon-check', 'uk-icon-clock-o') } /></td>
        
        <td  data-uk-tooltip="delay:500; pos: right" title={audit_message} className={"column_date_main 15"}>{date_complete}</td>


        <td className={"uk-hidden-small column_check 5" } ><i className={"uk-icon "  + yesorno(feedback,correct,enforce_answer_questions ) } />
        <i className={"uk-icon "  + yesorno(feedback,correct_by_deadline, enforce_answer_questions && enforce_deadline,'uk-icon-check','uk-icon-clock-o') } />
        </td>
        <td className={"uk-hidden-small column_date 15"}> { answer_deltat } </td>
        <td className={"uk-hidden-small column_check 5 "}><i className={"uk-icon "  + yesorno(feedback_safe,image_exists,enforce_image) } />
        <i className={"uk-icon "  + yesorno(feedback_safe,image_by_deadline,enforce_deadline && enforce_image , 'uk-icon-check', 'uk-icon-clock-o') } /></td>
        <td className={"uk-hidden-small column_date 15"}>
         { image_deltat }
        </td>
        <td className={"uk-hidden-small column_check 5"}   data-uk-tooltip="delay:500; pos: left" title={audit_message} > {points}  <i className={"uk-icon "  + yesorno(feedback_safe, audit_published,audit_published) } /> 
        <i className={"uk-icon "  + yesorno(feedback_safe,audit_passed,audit_published) } />  </td>
        <td> {points} </td>



        </tr>
        </tbody>
        </table>
    </div>
     ) }
   } else {
    
  return (
      <div className="uk-position-relative" data-uk-dropdown="{hoverDelayIdle: 0, delay: 300}">
        <a
          className={"uk-thumbnail exercise-a " + box_color }
          onClick={ev => onExerciseClick(exercise, foldername)}
        >
          <div className="exercise-thumb-wrap" style={{ minWidth: "80px", maxWidth: "100px" }}>
            <div className="exercise-thumb-badge">
              {meta.difficulty && <Badge className="uk-badge-notification"><T>{meta.difficulty}</T></Badge>}
              {meta.deadline_date && (
                <Badge className={"uk-badge-notification " + deadlineClass} title={legend}>
                  {moment(meta.deadline_date).format("D MMM")}
                </Badge>
              )}
              { dolegend && (
                <Badge className={"uk-badge-notification " + deadlineClass} title={'Recommended'}>
                  <T>{legend}</T>
                </Badge>
                    )
               }
                    
        
              {meta.image && (
                <span className={"uk-badge uk-badge-notification " + imageUploadClass}>
                  <i className="uk-icon uk-icon-camera" />
                </span>
              )}
              {meta.solution && <i className={ringClass} />}
              {showCheck && !meta.feedback && (
                  <span className="uk-badge uk-badge-notification">
                    <i className={"uk-icon "  + uk_icon_check } />
                  </span>
                )}
              {showCheck && meta.feedback && (
                  <span className={"uk-badge uk-badge-notification " + check_badge_color} >
                    <i className={"uk-icon " +  uk_icon_check} />
                  </span>
                )}
              {showResponseAwaits && <i className="uk-text-danger uk-margin-small-left uk-icon uk-icon uk-icon-envelope"/>}
              {exerciseState.getIn([exercise, "modified"]) && (
                <Badge className={"uk-badge-notification uk-badge-danger"}>
                  <i className="uk-icon uk-icon-save" />
                </Badge>
              )}
              {audit_published &&  (
                <Badge
                  type={ audit_revision_needed ? "error" : "success"}
                  className={"uk-badge-notification"} >granskad
                </Badge>
              )}
              {!meta.published && (
                <Badge type="error" title="Unpublished" className={"uk-badge-notification uk-float-right"}>
                  <T>Unpublished</T>
                </Badge>
              )}
            </div>
            <SafeImg className="exercise-thumb-nav" src={SUBPATH + "/exercise/" + exercise + "/asset/thumbnail.png"} />
          </div>
          <div className={"uk-thumbnail-caption exercise-thumb-nav-caption "}>
            <h4 className="uk-margin-remove">
              <T dict={nameDict}>{folder.getIn(["exercises", exercise, "name"])}</T>
            </h4>
          </div>
          {showStatistics &&
            !meta.deadline_date && (
              <div
                className="uk-progress uk-margin-remove uk-progress-small uk-progress-warning"
                title="blue: correct, orange: tried"
              >
                <div
                  className="uk-progress-bar"
                  style={{ width: percent_correct * 100 + "%", backgroundColor: "#00a8e6" }}
                />
                <div className="uk-progress-bar" style={{ width: (percent_tried - percent_correct) * 100 + "%" }} />
              </div>
            )}
          {showStatistics &&
            meta.deadline_date && (
              <div
                className="uk-progress uk-margin-remove uk-progress-small uk-progress-success"
                title="green: complete, blue: correct, orange: tried"
              >
                <div className="uk-progress-bar" style={{ width: percent_complete * 100 + "%" }} />
                <div
                  className="uk-progress-bar"
                  style={{ width: (percent_correct - percent_complete) * 100 + "%", backgroundColor: "#00a8e6" }}
                />
                <div
                  className="uk-progress-bar"
                  style={{ width: (percent_tried - percent_correct) * 100 + "%", backgroundColor: "#faa732" }}
                />
              </div>
            )}
          {activity >= 0 && (
            <div className="uk-progress uk-margin-remove uk-progress-small uk-progress-danger" title="Tries/Question">
              <div
                className="uk-progress-bar uk-text-small"
                style={{ width: activity + "%", backgroundColor: "#de96e2" }}
              >
                {activity >= 10 && (
                  <span className="uk-text-small">{exerciseState.getIn([exercise, "activity", activityRange])}</span>
                )}
                {activity < 10 &&
                  activity > 0 && (
                    <span style={{ position: "relative", left: "200%" }} className="uk-text-danger uk-text-small">
                      {exerciseState.getIn([exercise, "activity", activityRange])}
                    </span>
                  )}
                {activity == 0 && <span className="uk-text-primary uk-text-small">0</span>}
              </div>
            </div>
          )}
        </a>
        {  author && (
          <div className="uk-dropdown uk-dropdown-small uk-margin-remove" style={{ minWidth: 0 }}>
            <ExerciseHoverMenu exerciseKey={exercise} />
          </div>
        )}
      </div>
  );
 }

}

const mapStateToProps = state => ({
  exerciseState: state.get("exerciseState"),
  displaystyle: state.get("displaystyle"),
  showStatistics: state.getIn(["login", "groups"], immutable.List([])).includes("View"),
  statistics: state.get("statistics", immutable.Map({})),
  activityRange: state.get("activityRange", "1h"),
  student: state.getIn(["login", "groups"], immutable.List([])).includes("Student"),
  author: state.getIn(["login", "groups"], immutable.List([])).includes("Author"),
});


export default connect(
  mapStateToProps,
)(BaseExerciseItem);
