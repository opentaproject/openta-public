import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import T from './Translation.jsx';
import Cookies from 'universal-cookie';

import {
  updateDisplayStyle
} from '../actions.js';

const BaseUpdateDisplayStyle = ({displaystyle, onDisplayStyleChange}) => {
  var display={'horisontal': "IconView" , 'detail': "ListView"}
  var icon = 'uk-icon uk-icon-list'
  if ( displaystyle == 'horisontal' ){
        var newstyle = 'detail' 
        } else {
        var newstyle = 'horisontal'
        var icon = 'uk-icon uk-icon-th'
        }
  return ( 
        <a onClick={() =>  onDisplayStyleChange(newstyle)}>
        <button className="uk-button display-button uk-button uk-visible-toggle-@s">
            <i className={icon} />
        </button>
        </a>
            )
    }

const mapDispatchToProps = dispatch => {
    return {
        onDisplayStyleChange: (displaystyle) => {
            dispatch(updateDisplayStyle(displaystyle));
        }
    }
}

const mapStateToProps = (state) => {
  var cookies = new Cookies()
  var displaystyle =  state.getIn(['displaystyle'],'horisontal')
  cookies.set('DisplayStyle',  displaystyle  ,{path : '/'} )
    return {
      displaystyle :  displaystyle,
    };
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseUpdateDisplayStyle);
