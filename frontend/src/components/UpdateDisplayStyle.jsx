import React from 'react';
import { connect } from 'react-redux';
import Cookies from 'universal-cookie';

import { updateDisplayStyle } from '../actions.js';

const BaseUpdateDisplayStyle = ({ displaystyle, onDisplayStyleChange }) => {
  var display = { horisontal: 'IconView', detail: 'ListView' };
  var icon = 'uk-icon uk-icon-th';
  if (displaystyle == 'horisontal') {
    var newstyle = 'detail';
  } else {
    var newstyle = 'horisontal';
    var icon = 'uk-icon uk-icon-list';
  }
  return (
    <button
      type="button"
      className="uk-button display-button uk-visible-toggle-@s"
      onClick={() => onDisplayStyleChange(newstyle)}
    >
      <i className={icon} />
    </button>
  );
};

const mapDispatchToProps = (dispatch) => {
  return {
    onDisplayStyleChange: (displaystyle) => {
      dispatch(updateDisplayStyle(displaystyle));
    }
  };
};

const mapStateToProps = (state) => {
  var cookies = new Cookies();
  var displaystyle = state.getIn(['displaystyle'], 'horisontal');
  cookies.set('DisplayStyle', displaystyle, { path: '/', secure: true , sameSite : 'none'});
  return {
    displaystyle: displaystyle
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseUpdateDisplayStyle);
