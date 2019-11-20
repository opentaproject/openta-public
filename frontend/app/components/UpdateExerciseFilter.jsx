import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import T from './Translation.jsx';
import Cookies from 'universal-cookie';

import {
  updateExerciseFilter
} from '../actions.js';
import {
    fetchExerciseTree,
} from '../fetchers.js';


const BaseUpdateExerciseFilter = ({exercisefilter, onExerciseFilterChange,activeCourse}) => {
  console.log("BaseUpdateExerciseFilter exercifilter = ", exercisefilter)
  var icon_all = 'uk-icon uk-icon-pencil uk-icon-small'
  var icon_restrict = 'uk-icon uk-icon-minus-square uk-icon-small'
  var icon = icon_all
  var filter_toggle = 'published_exercises'
  if ( exercisefilter['published_exercises']  ){
      var icon = icon_restrict 
      }
  return ( 
        <a onClick={() =>  onExerciseFilterChange(exercisefilter,activeCourse,filter_toggle)} title='Toggle between showing and hiding unpublished'>
        <button className="uk-button uk-button-small display-button uk-button uk-visible-toggle-@s">
            <i className={icon} />
        </button>
        </a>
            )
    }

const mapDispatchToProps = dispatch => {
    console.log("DISPATCH" )
    return {
        onExerciseFilterChange: (exercisefilter,activeCourse,filter_toggle) => {
            exercisefilter[filter_toggle] = ! exercisefilter[filter_toggle]
            dispatch(updateExerciseFilter(exercisefilter))
            dispatch(fetchExerciseTree(activeCourse) )
        }
    }
}

const mapStateToProps = (state) => {
    return {
      exercisefilter : state.get('exercisefilter'),
      activeCourse :   state.get('activeCourse'),
    };
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseUpdateExerciseFilter);
