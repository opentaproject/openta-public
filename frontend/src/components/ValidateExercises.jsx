// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React from 'react';
import ReactHtmlParser from 'react-html-parser';
import { fetchExerciseTree, fetchExercise, fetchExerciseRemoteState } from '../fetchers.js';
import { navigateMenuArray, navigateAgain } from '../menu.js';
import { connect } from 'react-redux';
import { validateExercises } from '../fetchers.js';
import Exercise from './Exercise.jsx';
import AuthorExercise from './AuthorExercise';
import {} from '../actions.js';
import Spinner from './Spinner.jsx';
import DOMPurify from 'dompurify';


import immutable from 'immutable';

const BaseValidateExercises = ({ messages, pendingValidate, onPerformValidate, coursePk , onExerciseClick, exerciseState, admin, author,view }) => {
  var classDispatch = {
    error: 'uk-text-danger',
    info: 'uk-text-primary',
    warning: 'uk-text-warning',
    success: 'uk-text-success'
  };
  console.log("messages = ", messages.toJS()  )
  var imax = messages.size
  console.log("IMAX",imax)
  var rows = messages.map((item, index) => ( item.first  &&   index != 0 && index != imax - 1 &&  (
    <li className=''  key={index}>
	<a 
        onClick={() =>
            onExerciseClick(
	    item.first() ,
            exerciseState.getIn([item.first() , 'json'], immutable.Map({})).isEmpty()
          )
        }
      > 
      <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(item.last() ) }} />
	  
	  </a>
    </li> )
  ));
  <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(messages.last() ) }} />

  //var rows = messages.map( item => console.dir(item) );
  return (
	  <div className="uk-width-1-1" > 
    <div>
      {pendingValidate && (
        <span>
          <Spinner msg={'exercisesValidateing'} />
        </span>
      )}
	<div> <h4> Checking for validation errors in published exercsise </h4> </div> 	
      {!pendingValidate && ( <div> <ul className="uk-list">{rows}</ul>
	<span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(messages.last().last() ) }} />
	      </div> )
      }
    </div>
	  <AuthorExercise showXML={true} />
   </div>
  );
};

const mapStateToProps = (state) => {
  var exerciseState = state.getIn(['exerciseState'], immutable.Map({}));
  return {
  messages: state.get('exercisesValidateMessages', immutable.List([])),
  pendingValidate: state.getIn(['pendingState', 'exercisesValidate'], false),
  coursePk: state.get('activeCourse'),
    exerciselist: state.get('exercises', immutable.List([])),
    folder: state.get('folder', ''),
    activeExercise: state.get('activeExercise'),
    exerciseState: exerciseState,
    pendingState: state.get('pendingState'),
    showStatistics: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),


   admin: true, //  state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
  author: true , // state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
  view: true , // state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
  student: state.getIn(['login', 'groups'], immutable.List([])).includes('Student'),
  menuPath: state.get('menuPath'),
  compactview: state.getIn(['login', 'compactview'], true),
  anonymous: state.getIn(['login', 'groups'], immutable.List([])).includes('AnonymousStudent'),
  lti_login: state.getIn(['login', 'lti_login'], true),
  course_name: state.getIn(['course', 'course_name']),
  username: state.getIn(['login', 'username'])

  };
};


//const mapDispatchToProps = (dispatch) => ({
//  onPerformValidate: (coursePk) => dispatch(validateExercises(true, coursePk))
//});

const mapDispatchToProps = (dispatch) => {
  return {
   onPerformValidate: (coursePk) => dispatch(validateExercises(true, coursePk)),
    onExerciseClick: (exercise, empty) => {
      dispatch(fetchExercise(exercise, empty));
      dispatch(fetchExerciseRemoteState(exercise));
      dispatch(navigateAgain());
    },
    onBack: (coursePk) => dispatch(handleBack(coursePk))
  };
};



export default connect(mapStateToProps, mapDispatchToProps)(BaseValidateExercises);

