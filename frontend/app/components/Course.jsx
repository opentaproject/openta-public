import React, { Component } from 'react';
import PropTypes from 'prop-types';

import { connect } from "react-redux";
import {
  fetchExercise,
  fetchExerciseRemoteState,
  fetchExercises,
  fetchUserExercises,
  fetchSameFolder,
  fetchAddExercise,
  updatePendingStateIn,
  fetchCurrentAuditsExercise,
} from "../fetchers.js";


import {
  setActiveAudit,
  setResultsFilter,
  setDetailResultExercise,
  setDetailResultsView,
  updateExercises, 
 updateExerciseTreeUI,
} from '../actions.js';





import { navigateMenuArray } from "../menu.js";
import ExerciseItem from "./ExerciseItem.jsx";
import Spinner from "./Spinner.jsx";
import Badge from "./Badge.jsx";
import SafeImg from "./SafeImg.jsx";
import AddExercise from "./AddExercise.jsx";
import UpdateDisplayStyle from "./UpdateDisplayStyle.jsx";
import ExerciseHoverMenu from "./ExerciseHoverMenu.jsx";
import FolderHoverMenu from "./FolderHoverMenu.jsx";
import T from "./Translation.jsx";
import t from "../translations.js";

import immutable from "immutable";
import moment from "moment";
import { SUBPATH } from "../settings.js";

var difficulties = {
  "1": "Easy",
  "2": "Medium",
  "3": "Hard",
  none: ""
};


/* exercisetree, exerciseTreeUI, exerciseState, pendingState, currentpath, onExerciseClick,
  showStatistics, statistics, activityRange, onFolderClick, student, onExerciseAdd,
  pendingExerciseAdd, author, lti_login, displaystyle, user_pk */

class BaseCourse extends Component  {


 componentWillMount(props, state, root) {
    if ( this.props.user_pk && this.props.activeCourse ){
        fetchUserExercises(this.props.activeCourse,this.props.user_pk)
        }
    this.compact = this.props.compact || this.props.showStatistics
    if (this.props.onExerciseClick ){
        this.onExerciseClick = this.props.onExerciseClick
        } else {
        this.onExerciseClick = this.props.onDefaultExerciseClick
        }
        
  }

 //componentDidMount(props, state, root) {
 // }



flatten = (arr) =>  {
    return arr.reduce((flat, toFlat) => flat.concat(Array.isArray(toFlat) ? flatten(toFlat) : toFlat), []);
  }

countFinished = (folder, name, type)  => {
    if (folder.has("exercises")) {
      var results = folder
        .get("exercises")
        .filter(e => e.getIn(["meta", type]))
        .map((e, key) => this.props.exerciseState.getIn([key, "correct"], false));
      return {
        total: results.size,
        correct: results.filter(x => x).size
      };
    } else
      return {
        total: 0,
        correct: 0
      };
  }


parseFolder = (folder, foldername, level = 0, displaystyle)  => {
    var exercises = immutable.List([]),
      children = [];
    
    var rowbegin = ""
    var rowend = ""
    if ( displaystyle == 'detail' ){
        var rowbegin = "<tr>"
        var rowend= "</tr>"
        domstyle = ''
        }
    if (folder.has("exercises")) {
      exercises = folder.get("order").map(exercise => {
        var meta = folder.getIn(["exercises", exercise, "meta"]);
        var published = meta.get('published', false )
        if ( published || ( ! this.compact ) ){
        return (   <li className="course-exercise-item" key={exercise + 'asdf'} > 
 
           <ExerciseItem 
          exercise={exercise} 
          exerciseState={this.props.exerciseState}
          metaImmutable={meta} 
          folder={folder}
          compact={this.compact}
          foldername={foldername}
          onExerciseClick={this.onExerciseClick}
          showStatistics={this.props.showStatistics}
          statistics={this.props.statistics}
          activityRange={this.props.activityRange}
          displaystyle={displaystyle}
          author={this.props.author}  />
         </li>
            )
         }
        })
    }
    var add_exercise =  ( this.props.displaystyle  !== 'detail'  )  && ( ! this.compact  )
    var show_unpublished =  this.props.exercisefilter['unpublished_exercises'] 
    add_exercise = add_exercise && show_unpublished 
    if (   add_exercise ){
        exercises = exercises.push(  <AddExercise key="addExercise" path={folder.get("path")} />  );
    }
    if (folder.has("folders"))
      children = folder
        .get("folders", immutable.Map({}))
        .keySeq()
        .sort()
        .map(childfolder => ({
          name: childfolder,
          folder: folder.getIn(["folders", childfolder, "content"]),
          content: this.parseFolder(folder.getIn(["folders", childfolder, "content"]), childfolder, level + 1,this.props.displaystyle),
          path: folder.getIn(["folders", childfolder, "content", "path"]),
          folded: this.props.exerciseTreeUI.getIn(
            folder.getIn(["folders", childfolder, "content", "path"]).push("$folded$"),
            true
          ),
          pending: this.props.exerciseTreeUI.getIn(
            folder.getIn(["folders", childfolder, "content", "path"]).push("$pending$"),
            false
          )
        }));
    var levelClass = "";
    switch (level) {
      case 1:
        levelClass = "uk-block-muted";
        break;
      case 0:
        levelClass = "uk-block-muted";
        break;
    }
    var domstyle = "uk-thumbnav uk-flex uk-flex-bottom uk-padding-remove"
    if ( this.props.displaystyle == 'detail' ){
        var domstyle = 'uk-list uk-list-bullet uk-padding-remove uk-margin-remove'
        var use_header = true
        var foldertext = 'uk-text-medium uk-margin-remove uk-padding-remove  '
        } else {
        var foldertext = 'uk-text-large uk-margin-right'
        var use_header =  false
        }

    var minidom = (
        <div>
        <table className="uk-width-1-1 exercise_item">
        <tbody>
        <tr>
        <td className="uk-margin-remove uk-padding-remove uk-text-primary uk-text-bold column_name_head"> exercise name</td>
        <td className="uk-hidden-small uk-text-primary uk-text-bold column_date_due"> date due</td>
        <td className='uk-text-primary uk-text-bold column_date_plus'> complete and ontime </td>
        <td  className='uk-hidden-small uk-text-primary uk-text-bold column_date_plus'> autograded answers </td>
        <td  className='uk-hidden-small uk-text-primary uk-text-bold column_date_plus'> image answers </td>
        <td  className='uk-hidden-small column_check'> Audit</td>
        </tr>
        </tbody>
        </table>
        </div>
    )
  var spacedom = (
        <div>
        <table className="uk-width-1-1 exercise_item">
        <tbody>
        <tr>
        <td className="uk-margin-remove uk-padding-remove uk-text-primary uk-text-bold column_name_head"> </td>
        <td className="uk-hidden-small uk-text-primary uk-text-bold column_date_due"> </td>
        <td className='uk-text-primary uk-text-bold column_date_plus'> </td>
        <td  className='uk-hidden-small uk-text-primary uk-text-bold column_date_plus'> </td>
        <td  className='uk-hidden-small uk-text-primary uk-text-bold column_date_plus'> </td>
        <td  className='uk-hidden-small column_check'> </td>
        </tr>
        </tbody>
        </table>
        </div>
    )

  var DOMSUMMARY = (  <div>
         {level == 0 && use_header && (minidom) }
         {level == 0 && ! use_header && (spacedom) }
        </div>
    );


   var DOM = (


     <div className="uk-margin-remove uk-padding-remove">
          
      <div className={"uk-block uk-padding-remove " + levelClass}>
          {/* <div className="uk-visible-large uk-visible login-info"> VISIBLE</div>
          <div className="uk-visible-large uk-hidden login-info"> HIDDEN </div>
            */}
          <ul className={domstyle}>{exercises}</ul>
          <dl className="uk-description-list-horizontal uk-padding-remove uk-margin-remove">
            {children.map(child => {
              var folderPrename = child.name.split(".")[0].split(":");
              var folderName = folderPrename[folderPrename.length - 1];
              var folderClass = child.folded ? "uk-icon-folder" : "uk-icon-folder-open";
              var summaryReq = this.countFinished(child.folder, child.name, "required");
              if (summaryReq.total > 0) var percentReq = (100 * summaryReq.correct) / summaryReq.total;
              var summaryBonus = this.countFinished(child.folder, child.name, "bonus");
              if (summaryBonus.total > 0) var percentBonus = (100 * summaryBonus.correct) / summaryBonus.total;
              var rendered = [
                <dt 
                  className={foldertext}
                  style={{ float: "none", overflow: "visible", width: "auto" }}
                  key={"dt" + child.name}
                >
                  <div
                    className="uk-position-relative uk-display-inline"
                    data-uk-dropdown="{hoverDelayIdle: 0, delay: 300, pos: 'right-center'}"
                  >
                    <a onClick={() => this.props.onFolderClick(child.path, child.folded)}>
                      <i className={"uk-icon " + folderClass} />
                      {folderName === "Trash" && <i className="uk-icon uk-icon-trash uk-margin-small-left" />}
                      <span className="uk-margin-small-left">
                        <T>{folderName}</T>
                        {child.pending && <Spinner size=""  title='Spinner2' />}
                        {child.pending === null && <i className="uk-icon uk-icon-exclamation-triangle" />}
                      </span>
                    </a>
                    { this.props.author && (
                      <div
                        className="uk-dropdown uk-dropdown-small uk-margin-small"
                        style={{
                          minWidth: 0,
                          paddingLeft: "5px",
                          paddingRight: "5px",
                          paddingTop: 0,
                          paddingBottom: 0
                        }}
                      >
                        <FolderHoverMenu folderPath={child.path} />
                      </div>
                    )}
                  </div>
                </dt>
              ];
              if (!child.folded)
                rendered.push(
                  <dd className="uk-margin-left" key={"dd" + child.name}>
                    {" "}
                    {child.content}{" "}
                  </dd>
                );
              return rendered;
            })}
          </dl>
        </div>
      </div>
    );
    return (<div>  {DOMSUMMARY} {DOM} </div>
        )
  }
 
render() {
  if (this.props.pendingState.getIn(["course", "loadingExercises"], false)) {
    return <Spinner title='IF THIS KEEPS SPINNING, DISABLE THIRD PARTY COOKIES AND  UNSELECT CROSS-SITE TRACKING' />;
  }
  if (this.props.pendingState.getIn(['course', 'loadingExerciseTree'], false)) {
      return (<Spinner title='Spinner4' />);
  }
  if (this.props.exercisetree) {
    var top = this.parseFolder(this.props.exercisetree, "/", 0, this.props.displaystyle);
    return (
      <div className="uk-content-center">
        <ul className="uk-list">{top} </ul>
        </div>
    );
  }
  else {
    return (<Spinner title='Spinner5' />);
  }

 }
};


const handleAddExercise = path => dispatch => {
  console.dir("Will add exercise at " + path);
  return dispatch(fetchAddExercise(path));
};

const mapStateToProps = state => ({
  exerciseState: state.get("exerciseState"),
  pendingState: state.get("pendingState"),
  exercisetree: state.get("exerciseTree"),
  exerciseTreeUI: state.get("exerciseTreeUI"),
  displaystyle: state.get("displaystyle"),
  exercisefilter: state.getIn(["exercisefilter"],{'published_exercises':true, 
      'all_exercises': false, 
      'unpublished_exercises': true, 
      'required_exercises': true, 
      'optional_exericses': true,
      'bonus_exercises': true ,
      'FROM_COURSE' : true,} ),
  currentpath: state.get("currentpath"),
  showStatistics: state.getIn(["login", "groups"], immutable.List([])).includes("View"),
  statistics: state.get("statistics", immutable.Map({})),
  activityRange: state.get("activityRange", "1h"),
  student: state.getIn(["login", "groups"], immutable.List([])).includes("Student"),
  author: state.getIn(["login", "groups"], immutable.List([])).includes("Author"),
  lti_login: state.getIn(["login", "lti_login"], false ),
  activeCourse: state.get('activeCourse'),
});

const mapDispatchToProps = dispatch => ({
  onDefaultExerciseClick: (exercise, folder) => {
    dispatch(updatePendingStateIn(["exerciseList"], true));
    dispatch(fetchExerciseRemoteState(exercise))
      .then(dispatch(fetchExercise(exercise, true)))
      .then(dispatch(navigateMenuArray(["activeExercise"])));
    dispatch(updateExercises([], folder));
    dispatch(fetchSameFolder(exercise, folder));
  },

  //onExerciseClickFromResultsView: (exercise,folder) =>  {
  //  dispatch(setDetailResultExercise(exercise));
  //  dispatch(fetchExercise(exercise, true));
  // },

  
  onChangeView: (view) => dispatch(setDetailResultsView(view)),


  onFolderClick: (path, folded) => {
    var fullPath = immutable.List(path).push("$folded$");
    var updated = immutable.Map({}).setIn(fullPath, !folded);
    dispatch(updateExerciseTreeUI(updated));
  }
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(BaseCourse);
