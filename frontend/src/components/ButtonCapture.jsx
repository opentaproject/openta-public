// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React from 'react';
import { use_stars } from '../settings';
import { connect } from 'react-redux';
import immutable from 'immutable';

import { updateSelectedExercises } from '../actions/exercise';

import { updateExerciseTreeUI } from '../actions';

import { fetchExerciseTree } from '../fetchers';

// http://jsbin.com/nuhavu/1/edit?js,console,output

var unstableKey = 0;
const nextUnstableKey = () => unstableKey++;

class ButtonCapture extends React.Component {
  constructor() {
    super();
    this.state = { button: 0, stars: 0 , selected: false };
    this.handleChange = this.handleChange.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
  }

  handleChange = (e, exerciseKey, star = 0) => {
    //console.log("handleChange STAR = ", star )
    this.setState({ button: this.state.button + 1 }); // THIS DOES NOTHING BUT TRIGGER render
    var key = exerciseKey.toString();
    if (0 == e.buttons) {
      this.setState({ stars: this.state.stars == star ? 0 : star });
    }
    if (1 == e.buttons) {
      return this.props.children.props.onClick();
    }
    if (2 == e.buttons) {
      return this.props.onRightButtonClick(this.props.exerciseKey, this.props.activeCourse);
    }
  };

handleSelect= (e, exerciseKey, selected = false ) => {
    var key = exerciseKey.toString();
    this.setState({ selected : this.state.selected ==  ! selected });
    return this.props.onRightButtonClick(this.props.exerciseKey, this.props.activeCourse);
  };




  render() {
    const preventDefault = (e) => {
      e.preventDefault();
    };

    var names = ['Left', 'Right', 'Middle', 'Back', 'Forward'];

    // buttons is a bitmask
    var redBorder = {
      borderColor: 'rgb(255,131,0)',
      borderWidth: '4px',
      borderStyle: 'solid'
    };

    var yellowBorder = {
      borderColor: 'rgb(0,0,0)',
      borderWidth: '0px',
      borderStyle: 'solid'
    };

    var tablestyle = {
      borderCollapse: 'collapse'
    };

    var pad = '00000';
    //var buttons = this.bits(this.state.buttons,this.props.exerciseKey).concat([0, 0, 0, 0, 0]).slice(0, names.length);

    var do_use_stars = use_stars == 'true'; // enable starring is not fully impletmented and is disabled
    var selected = this.props.selectedExercises.includes(this.props.exerciseKey);
    var iconselected = selected ? 'uk-icon-check-circle-o' : 'uk-icon-circle-o';
    var selectedStyle = selected ? redBorder : yellowBorder;
    var organize = this.props.organize == undefined ? false : this.props.organize;
    var author = this.props.author;
    var headerbuttonclass = 'uk-button uk-button-default unpublished_exercises uk-button-link uk-button-mini';
    var selectbuttonclass = selected ? 'uk-button  uk-button-primary unpublished_exercises uk-button-mini' :  'uk-button  uk-button-default unpublished_exercises uk-button-mini' 

    //console.log("RENDER STARS = ", this.state.stars , "SELECTED = ", this.state.selectd)
    var iconstar1 = this.state.stars == 1 
        ? 'uk-icon uk-icon-circle uk-button-mini uk-padding-remove'
        : 'uk-icon uk-icon-circle-o uk-button-mini uk-padding-remove';
    var iconselected = selected 
        ? 'unselect'
        : 'select'
    var iconstar2 =
      this.state.stars == 2
        ? 'uk-icon uk-icon-star uk-button-mini uk-padding-remove'
        : 'uk-icon uk-icon-star-o uk-button-mini uk-padding-remove';
    var iconstar3 =
      this.state.stars == 3
        ? 'uk-icon uk-icon-star uk-button-mini uk-padding-remove'
        : 'uk-icon uk-icon-star-o uk-button-mini uk-padding-remove';
    var iconstar4 =
      this.state.stars == 4
        ? 'uk-icon uk-icon-star uk-button-mini uk-padding-remove'
        : 'uk-icon uk-icon-star-o uk-button-mini uk-padding-remove';
    var iconstar5 =
      this.state.stars == 5
        ? 'uk-icon uk-icon-star uk-button-mini uk-padding-remove'
        : 'uk-icon uk-icon-star-o uk-button-mini uk-padding-remove';

    return (
      <div>
	{ organize && (
		 <button
                            className={selectbuttonclass}
                            onClick={(e) => this.handleSelect(e, this.props.exerciseKey, this.props.selected )}
                          >
                            {iconselected}
                          </button>
	) }

        {organize && (
          <div style={selectedStyle} key={nextUnstableKey() + 'buttondiv'}>
            {author && (
              <table className="uk-table-condensed uk-table-small uk-table-justify" style={tablestyle}>
                <tbody>
                  <tr className="uk-padding-remove uk-margin-remove">
                    <td className="uk-padding-remove uk-margin-remove">
                      {do_use_stars && (
                        <span className="uk-button-group uk-button-mini uk-padding-remove" data-uk-button-radio>
                          <button
                            className={headerbuttonclass}
                            onClick={(e) => this.handleChange(e, this.props.exerciseKey, 1)}
                          >
                            {' '}
                            <i className={iconstar1} />{' '}
                          </button>
                          <button
                            className={headerbuttonclass}
                            onClick={(e) => this.handleChange(e, this.props.exerciseKey, 2)}
                          >
                            {' '}
                            <i className={iconstar2} />{' '}
                          </button>
                          <button
                            className={headerbuttonclass}
                            onClick={(e) => this.handleChange(e, this.props.exerciseKey, 3)}
                          >
                            {' '}
                            <i className={iconstar3} />{' '}
                          </button>
                          <button
                            className={headerbuttonclass}
                            onClick={(e) => this.handleChange(e, this.props.exerciseKey, 4)}
                          >
                            {' '}
                            <i className={iconstar4} />{' '}
                          </button>
                          <button
                            className={headerbuttonclass}
                            onClick={(e) => this.handleChange(e, this.props.exerciseKey, 5)}
                          >
                            {' '}
                            <i className={iconstar5} />{' '}
                          </button>
                        </span>
                      )}
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <span
                        //onContextMenu={preventDefault}
                        //onMouseDown={(e) => this.handleChange(e, this.props.exerciseKey, 5 )}
			onClick={(e) =>  this.props.children.props.onClick() }
                        tabIndex={-1}
                      >
                        <span key={nextUnstableKey() + 'buttondiv'}>{this.props.children} </span>
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            )}
            {!author && <span key={nextUnstableKey() + 'buttondiv'}> {this.props.children} </span>}
          </div>
        )}
        {!organize && this.props.children}
      </div>
    );
  }

  //const handleAddExercise = path => dispatch => {

  //bits = (n,exerciseKey) => {
  // this.props.onRightButtonClick( n, exerciseKey )
  //
  //
  // var res = [];
  // while(n){
  //   res.push(n & 1);
  //   n >>= 1;
  // }
  // return res;
  // }
}

const mapStateToProps = (state) => ({
  selectedExercises: state.getIn(['selectedExercises'], []),
  activeCourse: state.get('activeCourse'),
  author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author')
});

const mapDispatchToProps = (dispatch) => ({
  onRightButtonClick: (exerciseKey, activeCourse) => {
    dispatch(updateSelectedExercises(exerciseKey));
    dispatch(updateExerciseTreeUI(null)); // DONT KNOW IF THIS IS NEEDED
    dispatch(fetchExerciseTree(activeCourse));
  }
});

export default connect(mapStateToProps, mapDispatchToProps)(ButtonCapture);
