import React, { Component } from 'react';
import LanguageSelect from './LanguageSelect.jsx';
import { connect } from 'react-redux';
import { navigateMenuArray } from '../menu.js';
import Cookies from 'universal-cookie';

import immutable from 'immutable';
import { use_stars } from '../settings.js';
import { updateExerciseFilter } from '../actions.js';
import { fetchExerciseTree } from '../fetchers.js';
import PropTypes from 'prop-types';

class BaseSummaryBar extends Component {
  static propTypes = {
    exercisefilter: PropTypes.object,
    onExerciseFilterChange: PropTypes.func,
    show_edit_toggle: PropTypes.bool,
    author: PropTypes.bool,
    username: PropTypes.string,
    displaystyle: PropTypes.string,
    exerciseState: PropTypes.object,
    activeCourse: PropTypes.number
  };
  constructor() {
    super();
    this.state = {
      exercisefilter: {
        required_exercises: true,
        optional_exercises: true,
        bonus_exercises: true,
        unpublished_exercises: true,
        organize: false,
        star1: true,
        star2: true,
        star3: true,
        star4: true,
        star5: true
      }
    };
    this.handleFilterToggle = this.handleFilterToggle.bind(this);
  }

  componentDidMount(props, state, root) {
    this.setState({ exercisefilter: this.props.exercisefilter });
  }

  handleFilterToggle(exercisefilter, filter_toggle, activeCourse) {
    var newfilter = this.props.exercisefilter;
    newfilter[filter_toggle] = !newfilter[filter_toggle];
    this.setState({ exercisefilter: newfilter });
    this.props.onExerciseFilterChange(newfilter, activeCourse);
    var cookies = new Cookies();
    var clist = [];
    for (var entry in newfilter) {
      if (newfilter[entry] && entry !== 'undefined' && entry !== '') {
        clist.push(entry);
      }
    }
    cookies.set('exercisefilter', clist.join(';'), { path: '/', secure: true , sameSite: 'none' });
  }

  render() {
    //console.log("SHOW_EDIT_TOGGLE = ", show_edit_toggle )
    var show_edit_toggle = this.props.show_edit_toggle;
    //console.log("SHOW_EDIT_TOGGLE = ", show_edit_toggle )
    var exercisefilter = this.props.exercisefilter;
    var organize = exercisefilter.organize;
    var summary = this.props.exerciseState.getIn(['summary'], 'SUMMARY MISSING');
    var sums = this.props.exerciseState.getIn(['sums'], immutable.List([]));
    var sum01 = sums.getIn(['required', 'feedback', 'number_complete_by_deadline'], 0);
    var sum02 = sums.getIn(['required', 'feedback', 'number_complete'], 0) - sum01;
    var sum03 = sums.getIn(['required', 'nofeedback', 'number_complete_by_deadline'], 0);
    var sum04 = sums.getIn(['required', 'nofeedback', 'number_complete'], 0) - sum03;

    var sum11 = sums.getIn(['bonus', 'feedback', 'number_complete_by_deadline'], 0);
    var sum12 = sums.getIn(['bonus', 'feedback', 'number_complete'], 0) - sum11;
    var sum13 = sums.getIn(['bonus', 'nofeedback', 'number_complete_by_deadline'], 0);
    var sum14 = sums.getIn(['bonus', 'nofeedback', 'number_complete'], 0) - sum13;

    var sum21 = sums.getIn(['optional', 'feedback', 'number_complete_by_deadline'], 0);
    var sum22 = sums.getIn(['optional', 'feedback', 'number_complete'], 0) - sum21;
    var sum23 = sums.getIn(['optional', 'nofeedback', 'number_complete_by_deadline'], 0);
    var sum24 = sums.getIn(['optional', 'nofeedback', 'number_complete'], 0) - sum23;

    var mess0 = 'Required: ' + sum01 + ' correct and ontime ';
    mess0 = mess0 + (sum02 >= 1 ? ', ' + sum02 + 'correct but late ' : '');
    mess0 = mess0 + (sum03 >= 1 ? ', ' + sum03 + ' unchecked ontime ' : '');
    mess0 = mess0 + (sum04 >= 1 ? ', ' + sum04 + ' unchecked late ' : '');

    var mess1 = 'Bonus: ' + sum11 + ' correct and ontime ';
    mess1 = mess1 + (sum12 >= 1 ? ', ' + sum12 + 'correct but late ' : '');
    mess1 = mess1 + (sum13 >= 1 ? ', ' + sum13 + ' unchecked ontime ' : '');
    mess1 = mess1 + (sum14 >= 1 ? ', ' + sum14 + ' unchecked late ' : '');

    var mess2 = 'Optional: ' + sum21 + ' correct and ontime ';
    mess2 = mess2 + (sum22 >= 1 ? ', ' + sum22 + 'correct but late ' : '');
    mess2 = mess2 + (sum23 >= 1 ? ', ' + sum23 + ' unchecked ontime ' : '');
    mess2 = mess2 + (sum24 >= 1 ? ', ' + sum24 + ' unchecked late ' : '');

    var level = 0;
    var use_header = true;
    var runtests = this.props.exerciseState.getIn(['runtests'], false);
    var force_all_header_buttons = false;
    var author = this.props.author;
    var username = this.props.username;
    var min_answers_to_show_filter = 1;

    var show_obligatory = (sum01 + sum03 >= min_answers_to_show_filter) | runtests | force_all_header_buttons;
    var show_bonus = (sum11 + sum13 >= min_answers_to_show_filter) | runtests | force_all_header_buttons;
    var show_optional = (sum21 + sum23 >= min_answers_to_show_filter) | runtests | force_all_header_buttons;
    //console.log(show_obligatory, show_bonus, show_optional)
    var show_listview =
      true == ((true == (show_obligatory | show_bonus | show_optional)) | author | runtests | force_all_header_buttons);
    var show_logininfo_button = true == (author | runtests);
    var show_logininfo = true == ((true == sum11 + sum13 + sum01 + sum03 + sum21 + sum23 > 2) | author | runtests);
    var icon_required = 'uk-icon-check';
    var icon_optional = icon_required;
    var icon_bonus = icon_required;
    var icon_unpublished = icon_required;
    var iconoff = 'uk-icon-close';
    var iconview = !(this.props.displaystyle == 'detail');
    if (!exercisefilter.required_exercises) {
      icon_required = iconoff;
    }
    if (!exercisefilter.optional_exercises) {
      icon_optional = iconoff;
    }
    if (!exercisefilter.bonus_exercises) {
      icon_bonus = iconoff;
    }
    var show_unpublished = true;
    if (!exercisefilter.unpublished_exercises) {
      var icon_unpublished = 'uk-icon-toggle-off';
      var show_unpublished = false;
      var iconedit = 'uk-icon-circle-o';
    } else {
      var icon_unpublished = 'uk-icon-toggle-on';
      var iconedit = 'uk-icon-circle';
    }

    var iconorganize = organize ? 'uk-icon-circle' : 'uk-icon-circle-o';
    var iconstar1 = exercisefilter.star1 ? 'uk-icon-star' : 'uk-icon-star-o';
    var iconstar2 = exercisefilter.star2 ? 'uk-icon-star' : 'uk-icon-star-o';
    var iconstar3 = exercisefilter.star3 ? 'uk-icon-star' : 'uk-icon-star-o';
    var iconstar4 = exercisefilter.star4 ? 'uk-icon-star' : 'uk-icon-star-o';
    var iconstar5 = exercisefilter.star5 ? 'uk-icon-star' : 'uk-icon-star-o';

    var headerbuttonclass = 'uk-button uk-button-small  uk-button-default unpublished_exercises';
    var do_use_stars = use_stars == 'true';
    if (sum03 + sum04 > 0) {
      var psum034 = ':' + sum03 + ':' + sum04;
    } else {
      var psum034 = '';
    }
    if (sum13 + sum14 > 1) {
      var psum134 = ':' + sum13 + ':' + sum14;
    } else {
      var psum134 = '';
    }
    if (sum23 + sum24 > 1) {
      var psum234 = ':' + sum23 + ':' + sum24;
    } else {
      var psum234 = '';
    }
    //console.log("SUMMARY BAR")

    return (
      <span className="">
        <div className="uk-button-group">
          <LanguageSelect />
          {/*  author && ( <a className="uk-button" href=""> AAA </a> ) */}
          {show_edit_toggle && iconview && author && (
            <button
              onClick={() => this.handleFilterToggle(exercisefilter, 'unpublished_exercises', this.props.activeCourse)}
              data-uk-tooltip="delay:1500 ;   pos: right "
              className="uk-button uk-button-small  uk-button-default unpublished_exercises"
            >
              <i className={iconedit} /> ShowAll
            </button>
          )}
          {author && iconview && (
            <button
              onClick={() => this.handleFilterToggle(exercisefilter, 'organize', this.props.activeCourse)}
              data-uk-tooltip="delay:1500 ;   pos: right "
              className="uk-button uk-button-small  uk-button-default unpublished_exercises"
            >
              {' '}
              <i className={iconorganize} /> Organize
            </button>
          )}
          {show_obligatory && (
            <button
              onClick={() => this.handleFilterToggle(exercisefilter, 'required_exercises', this.props.activeCourse)}
              data-uk-tooltip="delay:1500 ;   pos: right "
              title={mess0}
              className="uk-button uk-button-small uk-text uk-text-small   blue required_exercises "
            >
              {' '}
              <i className={icon_required} /> {sum01}:{sum02}
              {psum034}{' '}
            </button>
          )}
          {show_bonus && (
            <button
              onClick={() => this.handleFilterToggle(exercisefilter, 'bonus_exercises', this.props.activeCourse)}
              data-uk-tooltip="delay:1500; pos: right"
              title={mess1}
              className="uk-button  uk-button-small   gold bonus_exercises "
            >
              {' '}
              <i className={icon_bonus} />
              {sum11}:{sum12}
              {psum134}{' '}
            </button>
          )}
          {show_optional && (
            <button
              onClick={() => this.handleFilterToggle(exercisefilter, 'optional_exercises', this.props.activeCourse)}
              data-uk-tooltip="delay:1500; pos: right"
              title={mess2}
              className="uk-button  uk-button-small  green optional_exercises "
            >
              {' '}
              <i className={icon_optional} />
              {sum21}:{sum22}
              {psum234}{' '}
            </button>
          )}
          {/* <button className="uk-button uk-hidden-small">{username}</button>  */}
          {do_use_stars && author && organize && (
            <span>
              <button
                className={headerbuttonclass}
                onClick={() => this.handleFilterToggle(exercisefilter, 'star1', this.props.activeCourse)}
              >
                {' '}
                <i className={iconstar1} />{' '}
              </button>
              <button
                className={headerbuttonclass}
                onClick={() => this.handleFilterToggle(exercisefilter, 'star2', this.props.activeCourse)}
              >
                {' '}
                <i className={iconstar2} />{' '}
              </button>
              <button
                className={headerbuttonclass}
                onClick={() => this.handleFilterToggle(exercisefilter, 'star3', this.props.activeCourse)}
              >
                {' '}
                <i className={iconstar3} />{' '}
              </button>
              <button
                className={headerbuttonclass}
                onClick={() => this.handleFilterToggle(exercisefilter, 'star4', this.props.activeCourse)}
              >
                {' '}
                <i className={iconstar4} />{' '}
              </button>
              <button
                className={headerbuttonclass}
                onClick={() => this.handleFilterToggle(exercisefilter, 'star5', this.props.activeCourse)}
              >
                {' '}
                <i className={iconstar5} />{' '}
              </button>
            </span>
          )}
        </div>
      </span>
    );
  }
}

const mapStateToProps = (state) => {
  var activeCourse = state.getIn(['activeCourse']);
  return {
    exerciseState: state.get('exerciseState'),
    displaystyle: state.get('displaystyle'),
    student: state.getIn(['login', 'groups'], immutable.List([])).includes('Student'),
    author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
    course: state.getIn(['courses', activeCourse, 'course_name'], ''),
    username: state.getIn(['exerciseState', 'username'], ''),
    iframed: state.getIn(['iframed'], false),
    exercisefilter: state.getIn(['exercisefilter']),
    activeCourse: state.get('activeCourse'),
    motd: state.getIn(['courses', activeCourse, 'motd'], '')
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    onHome: () => dispatch(navigateMenuArray([])),
    onExerciseFilterChange: (exercisefilter, activeCourse) => {
      dispatch(updateExerciseFilter(exercisefilter));
      dispatch(fetchExerciseTree(activeCourse));
    }
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseSummaryBar);
