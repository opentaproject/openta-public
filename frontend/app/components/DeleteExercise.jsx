import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import {navigateMenuArray} from '../menu.js';

import {
  fetchDeleteExercise,
  fetchExerciseTree
} from '../fetchers.js';

import {
  updatePendingStateIn,
  updateActiveExercise
} from '../actions.js';

const BaseDeleteExercise = ({onDelete, pendingDelete, exerciseKey, author}) => {
        if(!author)
            return (<span/>);
  return (
    <span className="uk-button uk-button-small uk-button-danger" title="Move exercise to trash." data-uk-tooltip onClick={() => onDelete(exerciseKey)}>
      <i className="uk-icon uk-icon-trash"/>
            { pendingDelete &&
              <Spinner/>
            }
            { pendingDelete === null &&
              <i className="uk-icon uk-icon-exclamation-triangle"/>
            }
    </span>
        );
    }

const mapDispatchToProps = dispatch => {
    return {
        onDelete: (exerciseKey) => {
            dispatch(updatePendingStateIn(['exercise', exerciseKey, 'delete'], true))
            dispatch(fetchDeleteExercise(exerciseKey))
                .then(() => dispatch(fetchExerciseTree()))
                .then( () => dispatch(updatePendingStateIn(['exercise', exerciseKey, 'delete'], false)))
                .then( () => dispatch(updateActiveExercise("")))
                .then( () =>dispatch(navigateMenuArray([])))
                .catch( err => {
                    console.dir(err);
                    dispatch(updatePendingStateIn(['exercise', exerciseKey, 'delete'], null))
                })
        }
    }
}

const mapStateToProps = (state) => {
    return {
        pendingExerciseAdd: state.getIn(['pendingState', 'course', 'addExercise']),
      author: state.getIn(['login', 'groups'],immutable.List([])).includes('Author'),
      exerciseKey: state.get('activeExercise')
    };
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseDeleteExercise);
